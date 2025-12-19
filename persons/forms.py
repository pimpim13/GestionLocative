from django import forms
from .models import Proprietaires, Locataires




class ProprietaireForm(forms.ModelForm):
    """Formulaire pour les propriétaires"""
    class Meta:
        model = Proprietaires

        fields = [
            'raison_sociale', 'nom', 'prenom', 'email', 'telephone', 'actif',
        ]
        widgets = {
            'raison-sociale' :  forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'téléphone': forms.TelInput(attrs={'class': 'form-control'}),
            'actif' : forms.CheckboxInput(attrs={'class': 'form-control'})
        }

class LocataireForm(forms.ModelForm):
    """Formulaire pour les locataires"""
    class Meta:
        model = Locataires

        fields = [
            'nom', 'prenom', 'email', 'telephone', 'notes', 'actif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'téléphonne': forms.TelInput(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-control'})
        }