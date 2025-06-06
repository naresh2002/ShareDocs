from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import User, File, Comment, AuthToken, FilePublicURL, SignedURL
import uuid
import json


# Helper functions
# Helper function to authenticate user from auth token
# Returns User object if valid token exists, None otherwise
def get_user_from_token(request):
    token = request.COOKIES.get('auth_token')
    if token:
        try:
            return AuthToken.objects.get(token=token).user
        except AuthToken.DoesNotExist:
            return None
    return None

# Authentication views
# Home page view
# @param request: HTTP request object
# @return: Renders home page with user context
def home(request):
    user = get_user_from_token(request)
    return render(request, 'home.html', {'user': user})

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = make_password(request.POST['password'])

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email already exists in database, please choose a different email'})

        User.objects.create(username=username, email=email, password=password)
        return redirect('/login/')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password):
                token = str(uuid.uuid4())
                AuthToken.objects.create(user=user, token=token)
                response = redirect('/')
                response.set_cookie('auth_token', token)
                return response
            else:
                raise ValueError("Invalid password, please try again!")
        except:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    token = request.COOKIES.get('auth_token')
    if token:
        AuthToken.objects.filter(token=token).delete()
    response = redirect('/')
    response.delete_cookie('auth_token')
    return response

# File management views
# Upload a new file
# @param request: HTTP request object
# @return: Renders upload form or redirects to my_files on success
def upload_file(request):
    user = get_user_from_token(request)
    if not user:
        return redirect('/login/')

    error = None
    if request.method == 'POST' and 'file' in request.FILES:
        uploaded_file = request.FILES['file']

        # Validate content type
        if uploaded_file.content_type != 'application/pdf':
            error = "Only PDF files are allowed."
        # Optional: double-check the file extension
        elif not uploaded_file.name.lower().endswith('.pdf'):
            error = "The file must have a .pdf extension."

        if not error:
            # Save the uploaded file
            saved_path = default_storage.save(uploaded_file.name, uploaded_file)

            # Create File model instance with saved path
            File.objects.create(name=saved_path, owner=user.username)
            return redirect('/my_files/')  # Optional: redirect after successful upload

    return render(request, 'upload_file.html', {'user': user, 'error': error})

def my_files(request):
    user = get_user_from_token(request)
    if not user:
        return redirect('/login/')
    files = File.objects.filter(owner=user.username)
    return render(request, 'my_files.html', {'files': files, 'user': user})

def view_file(request, file_id):
    user = get_user_from_token(request)
    file = get_object_or_404(File, id=file_id)

    # Check if the file is made public
    try:
        public_record = FilePublicURL.objects.get(file=file)
    except FilePublicURL.DoesNotExist:
        public_record = None

    is_public = public_record.is_public if public_record else False

    # Deny access if not public and not owner
    if file.owner != (user.username if user else None) and not is_public:
        return render(request, 'access_denied.html', {'user': user})

    # Fetch comments
    comments = Comment.objects.filter(file_id=file, parent_comment_id=None).order_by('created_at')

    # Get temporary shared URL if redirected after link generation
    shared_token = None
    if request.GET.get('shared') == '1':
        shared_token = request.session.pop('shared_token', None)

    if request.method == 'POST':
        if not user:
            return JsonResponse({'error': 'Login required'}, status=401)

        data = json.loads(request.body)
        text = data.get('comment_text')
        parent_id = data.get('parent_comment_id')
        parent_comment = Comment.objects.get(id=parent_id) if parent_id else None
        Comment.objects.create(user=user.username, file_id=file, parent_comment_id=parent_comment, comment_text=text)
        return JsonResponse({'success': True, 'comment_user': user.username})

    return render(request, 'view_file.html', {
        'file': file,
        'comments': comments,
        'user': user,
        'is_public': is_public,
        'shared_token': shared_token,
        'request': request
    })

# File sharing views
# Toggle file visibility between public/private
# @param request: HTTP request object
# @param file_id: ID of the file to toggle visibility for
# @return: Redirects to file view page
@csrf_exempt
def toggle_visibility(request, file_id):
    user = get_user_from_token(request)
    file = get_object_or_404(File, id=file_id)

    if not user or file.owner != user.username:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    public_record, created = FilePublicURL.objects.get_or_create(file=file)
    public_record.is_public = not public_record.is_public
    public_record.save()
    return redirect(f'/view_file/{file_id}/')

# Generate a temporary shareable link for a file
# @param request: HTTP request object
# @param file_id: ID of the file to share
# @return: Redirects to file view page with shared token
@csrf_exempt
def share_file(request, file_id):
    user = get_user_from_token(request)
    file = get_object_or_404(File, id=file_id)

    if not user or user.username != file.owner:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        recipient_name = request.POST.get('recipient_name')
        if not recipient_name:
            return redirect(f'/view_file/{file_id}/')

        token = get_random_string(20)
        expires_at = timezone.now() + timezone.timedelta(days=14)

        SignedURL.objects.create(
            file=file,
            recipient_name=recipient_name,
            signed_url=token,
            expires_at=expires_at
        )

        request.session['shared_token'] = token
        return redirect(f'/view_file/{file_id}/?shared=1')

def shared_file(request, token):
    signed = get_object_or_404(SignedURL, signed_url=token)
    if signed.is_expired():
        return render(request, 'link_expired.html')

    file = signed.file
    comments = Comment.objects.filter(file_id=file, parent_comment_id=None).order_by('created_at')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('comment_text')
            parent_id = data.get('parent_comment_id')
            parent_comment = Comment.objects.get(id=parent_id) if parent_id else None

            Comment.objects.create(user=signed.recipient_name, file_id=file, parent_comment_id=parent_comment, comment_text=text)
            return JsonResponse({'success': True, 'comment_user': signed.recipient_name})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'shared_file.html', {
        'file': file,
        'comments': comments,
        'recipient': signed.recipient_name,
    })