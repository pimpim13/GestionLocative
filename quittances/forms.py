# quittances/forms.py
from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .models import Quittance
from contrats.models import Contrats
from immeuble.models import Immeuble
from datetime import date


class QuittanceGenerationForm(forms.Form):
    """Formulaire pour générer une quittance"""

    mois = forms.DateField(
        label="Mois concerné",
        widget=DatePickerInput(
            format='%d/%m/%Y',
            options={
                "locale": "fr",
                "viewMode": "months",
                "format": "MM/YYYY",
                "showClose": True,
                "showClear": True,
            }
        ),
        help_text="Sélectionnez le mois pour lequel générer la quittance"
    )

    force_regeneration = forms.BooleanField(
        label="Forcer la régénération",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Cochez pour régénérer même si une quittance existe déjà"
    )

    def clean_mois(self):
        mois = self.cleaned_data['mois']

        # Convertir en premier jour du mois
        mois = mois.replace(day=1)

        # Vérifier que ce n'est pas dans le futur
        if mois > date.today().replace(day=1):
            raise forms.ValidationError(
                "Impossible de générer une quittance pour un mois futur."
            )

        return mois


class QuittanceBatchForm(forms.Form):
    """Formulaire pour génération en lot"""

    mois = forms.DateField(
        label="Mois concerné",
        widget=DatePickerInput(
            format='%d/%m/%Y',
            options={
                "locale": "fr",
                "viewMode": "months",
                "format": "MM/YYYY",
            }
        )
    )

    immeubles = forms.ModelMultipleChoiceField(
        queryset=Immeuble.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Immeubles (laisser vide pour tous)",
        help_text="Sélectionnez les immeubles concernés"
    )

    uniquement_payes = forms.BooleanField(
        label="Uniquement les loyers payés",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Ne générer que pour les contrats avec paiement enregistré"
    )

    def clean_mois(self):
        mois = self.cleaned_data['mois']
        return mois.replace(day=1)


class QuittanceSearchForm(forms.Form):
    """Formulaire de recherche des quittances"""

    search = forms.CharField(
        required=False,
        label="Rechercher",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom, prénom, numéro de quittance...'
        })
    )

    immeuble = forms.ModelChoiceField(
        queryset=Immeuble.objects.all(),
        required=False,
        empty_label="Tous les immeubles",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    mois = forms.DateField(
        required=False,
        label="Mois",
        widget=DatePickerInput(
            format='%d/%m/%Y',
            options={
                "locale": "fr",
                "viewMode": "months",
                "format": "MM/YYYY",
            }
        )
    )

    envoyee = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Toutes'),
            ('1', 'Envoyées'),
            ('0', 'Non envoyées'),
        ],
        label="Statut d'envoi",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class QuittanceManuelleForm(forms.ModelForm):
    """Formulaire pour créer une quittance manuellement"""

    class Meta:
        model = Quittance
        fields = ['contrat', 'mois', 'loyer', 'charges', 'notes']
        widgets = {
            'contrat': forms.Select(attrs={'class': 'form-select'}),
            'mois': DatePickerInput(
                format='%d/%m/%Y',
                options={
                    "locale": "fr",
                    "viewMode": "months",
                    "format": "MM/YYYY",
                }
            ),
            'loyer': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Labels
        self.fields['mois'].label = "Mois concerné"
        self.fields['loyer'].label = "Loyer hors charges (€)"
        self.fields['charges'].label = "Charges (€)"

        # Filtrer uniquement les contrats actifs
        self.fields['contrat'].queryset = Contrats.objects.filter(
            actif=True
        ).select_related('locataire', 'appartement__immeuble')

        # Personnaliser l'affichage des contrats
        self.fields['contrat'].label_from_instance = lambda obj: (
            f"{obj.locataire.nom_complet} - "
            f"{obj.appartement.immeuble.nom} Apt {obj.appartement.numero}"
        )

        # Pré-remplir avec les valeurs du contrat si création
        if not self.instance.pk and 'contrat' in self.initial:
            contrat_id = self.initial.get('contrat')
            try:
                contrat = Contrats.objects.get(pk=contrat_id)
                self.fields['loyer'].initial = contrat.loyer_mensuel
                self.fields['charges'].initial = contrat.charges_mensuelles
            except Contrats.DoesNotExist:
                pass

    def clean_mois(self):
        mois = self.cleaned_data['mois']
        return mois.replace(day=1)

    def clean(self):
        cleaned_data = super().clean()
        contrat = cleaned_data.get('contrat')
        mois = cleaned_data.get('mois')

        # Vérifier qu'il n'y a pas déjà une quittance
        if contrat and mois:
            existing = Quittance.objects.filter(
                contrat=contrat,
                mois=mois
            )

            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    f"Une quittance existe déjà pour {mois.strftime('%B %Y')}."
                )

        return cleaned_data