from django import forms
from .models import Contrats
from bootstrap_datepicker_plus.widgets import DatePickerInput

class ContratForm(forms.ModelForm):
    """Formulaire pour les propriétaires"""
    class Meta:
        model = Contrats
        # exclude = ['id', 'created_at','updated_at']
        # fields = ['__all__']
        # widgets = {
        #     'raison-sociale' :  forms.TextInput(attrs={'class': 'form-control'}),
        #     'nom': forms.TextInput(attrs={'class': 'form-control'}),
        #     'prenom': forms.TextInput(attrs={'class': 'form-control'}),
        #     'email': forms.EmailInput(attrs={'class': 'form-control'}),
        #     'téléphone': forms.TelInput(attrs={'class': 'form-control'}),
        #     'actif' : forms.CheckboxInput(attrs={'class': 'form-control'})
        # }
        fields = [
            'locataire', 'appartement', 'date_debut', 'date_fin',
            'date_fin_effective', 'loyer_mensuel', 'charges_mensuelles',
            'depot_garantie', 'indice_reference', 'date_revision',
            'date_preavis', 'actif', 'preavis_donne', 'notes'
        ]
        widgets = {
            # Sélecteurs de date
            'date_debut': DatePickerInput(
                options={
                    "format": "DD/MM/YYYY",
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            'date_fin': DatePickerInput(
                options={
                    "format": "DD/MM/YYYY",
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                }
            ),
            'date_fin_effective': DatePickerInput(
                options={
                    "format": "DD/MM/YYYY",
                    "locale": "fr",
                }
            ),
            'date_revision': DatePickerInput(
                options={
                    "format": "DD/MM/YYYY",
                    "locale": "fr",
                }
            ),
            'date_preavis': DatePickerInput(
                options={
                    "format": "DD/MM/YYYY",
                    "locale": "fr",
                }
            ),
            # Autres champs
            'locataire': forms.Select(attrs={'class': 'form-select'}),
            'appartement': forms.Select(attrs={'class': 'form-select'}),
            'loyer_mensuel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'charges_mensuelles': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'depot_garantie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'indice_reference': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'preavis_donne': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
