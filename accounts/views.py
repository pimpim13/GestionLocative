from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

# Create your views here.

def user_is_admin(user):
    """Vérifie si l'utilisateur est admin"""
    return user.is_authenticated and (user.is_superuser or user.fonction == 'proprietaire')

def user_is_gestionnaire_or_admin(user):
    """Vérifie si l'utilisateur est gestionnaire ou admin"""
    return user.is_authenticated and user.fonction in ['proprietaire', 'gestionnaire']

# Décorateurs personnalisés
admin_required = user_passes_test(user_is_admin)
gestionnaire_required = user_passes_test(user_is_gestionnaire_or_admin)




def custom_login_view(request):

    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
        else:
            messages.warning(request, 'identifiant ou mot de passe incorrect')

    return redirect('home')

def custom_logout_view(request,):
    logout(request)
    return redirect('home')




def profile_view(request):
    return HttpResponse('ProfileView')

def create_user_view(request):
    return HttpResponse('create_user View')