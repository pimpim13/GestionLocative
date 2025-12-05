#src/authentication.py

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from accounts.models import CustomUser

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
    """Vue de connexion personnalisée"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue { user.username} !')
                # messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')

                # Redirection selon le rôle
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                elif user.fonction == 'proprietaire':
                    return redirect('dashboard_admin')
                else:
                    return redirect('dashboard')
            else:
                messages.error(request, 'Identifiants incorrects.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

def custom_logout_view(request):
    """Vue de déconnexion personnalisée"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'registration/profile.html', {'form': form})

@admin_required
def create_user_view(request):
    """Vue de création d'utilisateur (admin seulement)"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Utilisateur {user.username} créé avec succès.')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/create_user.html', {'form': form})