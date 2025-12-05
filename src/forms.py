#src/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from accounts.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Formulaire de création d'utilisateur personnalisé"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")
    telephone = forms.CharField(max_length=20, required=False, label="Téléphone")
    fonction = forms.ChoiceField(
        choices=CustomUser._meta.get_field('fonction').choices,
        required=True
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'telephone', 'fonction')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.telephone = self.cleaned_data['telephone']
        user.fonction = self.cleaned_data['fonction']
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion personnalisé"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Formulaire de profil utilisateur"""

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone', 'adresse']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }