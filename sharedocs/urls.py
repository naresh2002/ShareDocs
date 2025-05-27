from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('signup/', views.signup_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('upload/', views.upload_file),
    path('my_files/', views.my_files),
    path('view_file/<uuid:file_id>/', views.view_file),
    path('toggle_visibility/<uuid:file_id>/', views.toggle_visibility),
    path('share_file/<uuid:file_id>/', views.share_file, name='share_file'),
    path('shared_file/<str:token>/', views.shared_file, name='shared_file'),
]
