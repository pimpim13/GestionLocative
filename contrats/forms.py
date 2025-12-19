# contrats/forms.py
from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .models import Contrats, ContratLocataire
from persons.models import Locataires
from immeuble.models import Appartement


class ContratForm(forms.ModelForm):
    """Formulaire pour créer/modifier un contrat"""

    class Meta:
        model = Contrats
        fields = [
            'appartement', 'date_debut', 'date_fin',
            'loyer_mensuel', 'charges_mensuelles', 'jour_echeance', 'depot_garantie',
            'indice_reference', 'date_revision', 'notes', 'actif', 'fichier_contrat',
            'preavis_donne', 'date_preavis', 'etat_lieux_entree', 'etat_lieux_sortie'
        ]
        widgets = {
            'date_debut': DatePickerInput(
                options={
                    "format": 'DD-MM-YYYY',
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            'date_fin': DatePickerInput(
                options={
                    "format": 'DD-MM-YYYY',
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                }
            ),
            'date_revision': DatePickerInput(
                options={
                    "format": 'DD-MM-YYYY',
                    "locale": "fr",
                }
            ),
            'date_preavis': DatePickerInput(
                options={
                    "format": 'DD-MM-YYYY',
                    "locale": "fr",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personnalisation des labels et help texts
        self.fields['date_debut'].label = "Date de début du bail"
        self.fields['date_fin'].label = "Date de fin prévue"
        self.fields['loyer_mensuel'].label = "Loyer mensuel (€)"
        self.fields['charges_mensuelles'].label = "Charges mensuelles (€)"
        self.fields['jour_echeance'].label = "Jour d'échéance du loyer"
        self.fields['jour_echeance'].help_text = "Jour du mois où le loyer doit être payé (1-31)"

        # Rendre certains champs non obligatoires
        self.fields['date_fin'].required = False
        self.fields['indice_reference'].required = False
        self.fields['date_revision'].required = False
        self.fields['date_preavis'].required = False


class ContratLocataireForm(forms.ModelForm):
    """Formulaire pour ajouter/modifier un locataire sur un contrat"""

    class Meta:
        model = ContratLocataire
        fields = [
            'locataire', 'principal', 'ordre',
            'date_entree', 'date_sortie', 'role', 'notes'
        ]
        widgets = {
            'date_entree': DatePickerInput(
                options={
                    "format": 'DD-MM-YYYY',
                    "locale": "fr",
                    "showClose": True,
                    "showTodayButton": True,
                }
            ),
            'date_sortie': DatePickerInput(
                options={
                    "format": 'DD-MM-YYYY',
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                }
            ),
            'locataire': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        contrat = kwargs.pop('contrat', None)
        super().__init__(*args, **kwargs)

        # Personnalisation
        self.fields['locataire'].label = "Locataire"
        self.fields['principal'].label = "Contact principal"
        self.fields['principal'].help_text = "Cochez si c'est le locataire à contacter en priorité"
        self.fields['ordre'].label = "Ordre d'affichage"
        self.fields['ordre'].help_text = "1 pour le premier, 2 pour le second, etc."
        self.fields['date_entree'].label = "Date d'entrée dans le bail"
        self.fields['date_sortie'].label = "Date de sortie du bail"
        self.fields['date_sortie'].help_text = "Laisser vide si toujours sur le bail"
        self.fields['role'].label = "Rôle"

        # Pré-remplir la date d'entrée avec celle du contrat
        if contrat and not self.instance.pk:
            self.fields['date_entree'].initial = contrat.date_debut

        # Rendre certains champs non obligatoires
        self.fields['date_sortie'].required = False
        self.fields['notes'].required = False
        self.fields['ordre'].initial = 1

    def clean(self):
        cleaned_data = super().clean()
        date_entree = cleaned_data.get('date_entree')
        date_sortie = cleaned_data.get('date_sortie')

        # Vérifier que date_sortie > date_entree
        if date_entree and date_sortie and date_sortie <= date_entree:
            raise forms.ValidationError(
                "La date de sortie doit être postérieure à la date d'entrée"
            )

        return cleaned_data


class AjouterLocataireContratForm(forms.Form):
    """Formulaire simplifié pour ajouter rapidement un locataire à un contrat"""

    locataire = forms.ModelChoiceField(
        queryset=Locataires.objects.filter(actif=True).order_by('nom', 'prenom'),
        label="Sélectionner un locataire",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="-- Choisir un locataire --"
    )

    principal = forms.BooleanField(
        required=False,
        label="Définir comme contact principal",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    role = forms.ChoiceField(
        choices=ContratLocataire._meta.get_field('role').choices,
        initial='cotitulaire',
        label="Rôle",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        contrat = kwargs.pop('contrat', None)
        super().__init__(*args, **kwargs)

        # Exclure les locataires déjà sur ce contrat
        if contrat:
            locataires_existants = contrat.locataires.values_list('id', flat=True)
            self.fields['locataire'].queryset = Locataires.objects.filter(
                actif=True
            ).exclude(
                id__in=locataires_existants
            ).order_by('nom', 'prenom')


class CreerNouveauLocataireForm(forms.ModelForm):
    """Formulaire pour créer un nouveau locataire et l'ajouter au contrat"""

    class Meta:
        model = Locataires
        fields = ['nom', 'prenom', 'email', 'telephone', 'notes']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    principal = forms.BooleanField(
        required=False,
        label="Définir comme contact principal",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    role = forms.ChoiceField(
        choices=ContratLocataire._meta.get_field('role').choices,
        initial='cotitulaire',
        label="Rôle dans le contrat",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# Formset pour gérer plusieurs locataires en une seule fois
from django.forms import inlineformset_factory

ContratLocataireFormSet = inlineformset_factory(
    Contrats,
    ContratLocataire,
    form=ContratLocataireForm,
    extra=1,  # Nombre de formulaires vides affichés
    can_delete=True,  # Permet de supprimer
    min_num=1,  # Minimum 1 locataire requis
    validate_min=True
)