from django import forms
from .models import Immeuble, Appartement #, TypeAppartement

class ImmeubleForm(forms.ModelForm):
    """Formulaire pour les immeubles"""
    class Meta:
        model = Immeuble

        fields = [
            'nom', 'adresse', 'ville', 'code_postal',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
            'code_postal': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AppartementForm(forms.ModelForm):
    """Formulaire pour les appartements"""
    class Meta:
        model = Appartement
        fields = [
            'immeuble', 'numero', 'etage', 'proprietaire' , 'surface', 'milliemes'
        ]
        widgets = {
            'immeuble': forms.Select(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'proprietaire': forms.Select(attrs={'class': 'form-control'}),
            'etage': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'loué': forms.CheckboxInput(attrs={'class': 'form-control'}),
        }

class ImmeubleSearchForm(forms.Form):
    """Formulaire de recherche d'immeubles"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, ville ou adresse...'
        })
    )


class ImmeubleCreateForm(forms.ModelForm):

    class Meta:
        model = Immeuble
        fields = ['nom', 'adresse', 'code_postal', 'ville']
