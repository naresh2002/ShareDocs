from functools import wraps
from rest_framework.response import Response
from .models import AuthToken
from django.utils import timezone

def token_required(view_func):
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': 'Unauthorized'}, status=401)

        token_str = auth_header.split()[1]
        try:
            token = AuthToken.objects.get(token=token_str)
            if not token.is_valid():
                return Response({'error': 'Token expired'}, status=401)
            request.user = token.user
        except AuthToken.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=401)

        return view_func(self, request, *args, **kwargs)
    return wrapper
