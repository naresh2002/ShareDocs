from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage

from django.utils import timezone
from .models import User, File, Comment, AuthToken, FilePublicURL
import uuid
import json

def get_user_from_token(request):
    token = request.COOKIES.get('auth_token')
    if token:
        try:
            return AuthToken.objects.get(token=token).user
        except AuthToken.DoesNotExist:
            return None
    return None

from django.views.decorators.csrf import csrf_exempt

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


def home(request):
    user = get_user_from_token(request)
    return render(request, 'home.html', {'user': user})

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = make_password(request.POST['password'])

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email already exists'})

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
                raise ValueError("Invalid password")
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

def upload_file(request):
    user = get_user_from_token(request)
    if not user:
        return redirect('/login/')

    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        # Save file using default storage (S3)
        saved_path = default_storage.save(uploaded_file.name, uploaded_file)

        # Create model instance with saved path
        File.objects.create(name=saved_path, owner=user.username)
    return render(request, 'upload_file.html', {'user': user})

# def upload_file(request):
#     user = get_user_from_token(request)
#     if not user:
#         return redirect('/login/')

#     if request.method == 'POST':
#         uploaded_file = request.FILES.get('file')
#         if not uploaded_file:
#             return render(request, 'upload_file.html', {'user': user, 'error': 'No file uploaded'})

#         try:
#             # Save the file using the model directly
#             File.objects.create(name=uploaded_file, owner=user.username)
#             return redirect('/my_files/')
#         except Exception as e:
#             import traceback
#             tb = traceback.format_exc()
#             return render(request, 'upload_file.html', {'user': user, 'error': f"Error saving file: {str(e)}", 'traceback': tb})

#     return render(request, 'upload_file.html', {'user': user})

def my_files(request):
    user = get_user_from_token(request)
    if not user:
        return redirect('/login/')
    files = File.objects.filter(owner=user.username)
    return render(request, 'my_files.html', {'files': files, 'user': user})


def view_file(request, file_id):
    user = get_user_from_token(request)
    file = get_object_or_404(File, id=file_id)
    
    # Access control
    try:
        public_record = FilePublicURL.objects.get(file=file)
    except FilePublicURL.DoesNotExist:
        public_record = None

    is_public = public_record.is_public if public_record else False

    if file.owner != (user.username if user else None) and not is_public:
        return render(request, 'access_denied.html', {'user': user})

    comments = Comment.objects.filter(file_id=file, parent_comment_id=None).order_by('created_at')

    if request.method == 'POST':
        if not user:
            return JsonResponse({'error': 'Login required'}, status=401)

        data = json.loads(request.body)
        text = data.get('comment_text')
        parent_id = data.get('parent_comment_id')
        parent_comment = Comment.objects.get(id=parent_id) if parent_id else None
        Comment.objects.create(user=user.username, file_id=file, parent_comment_id=parent_comment, comment_text=text)
        return JsonResponse({'success': True})

    return render(request, 'view_file.html', {
        'file': file,
        'comments': comments,
        'user': user,
        'is_public': is_public
    })
