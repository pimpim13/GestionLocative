from django.contrib import admin
from django.urls import path, include


from .views import custom_login_view, custom_logout_view, profile_view, create_user_view

app_name = 'accounts'

urlpatterns = [

    path('login/', custom_login_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('users/create/', create_user_view, name='create_user'),

    ]
