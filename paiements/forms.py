# paiements/forms.py
from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .models import PaiementLocataire
from contrats.models import Contrats
from datetime import date

class PaiementLocataireForm(forms.ModelForm):
    class Meta:
        model = PaiementLocataire
        fields = [
            'contrat', 'mois', 'loyer', 'charges', 'autres',
            'date_paiement', 'date_echeance', 'mode_paiement',
            'reference', 'statut', 'valide', 'notes'
        ]
        widgets = {
            # Sélecteurs de date
            'mois': DatePickerInput(
                format='%d/%m/%Y',
                options={
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                    "viewMode": "months",
                    "format": "MM/YYYY",
                }
            ),
            'date_paiement': DatePickerInput(
                format='%d/%m/%Y',
                options={
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            'date_echeance': DatePickerInput(
                format='%d/%m/%Y',
                options={
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                }
            ),

            # Autres widgets
            'contrat': forms.Select(attrs={
                'class': 'form-select',
                'data-live-search': 'true'
            }),
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
            'autres': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'mode_paiement': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° chèque, référence virement...'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            }),
            'valide': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes ou observations...'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Récupérer des arguments optionnels
        contrat_id = kwargs.pop('contrat_id', None)
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # Personnalisation des labels
        self.fields['mois'].label = "Mois concerné"
        self.fields['loyer'].label = "Loyer payé (€)"
        self.fields['charges'].label = "Charges payées (€)"
        self.fields['autres'].label = "Autres montants (€)"
        self.fields['date_paiement'].label = "Date du paiement"
        self.fields['date_echeance'].label = "Date d'échéance"
        self.fields['mode_paiement'].label = "Mode de paiement"
        self.fields['reference'].label = "Référence"
        self.fields['statut'].label = "Statut du paiement"
        self.fields['valide'].label = "Paiement validé"

        # Help texts
        self.fields['mois'].help_text = "Premier jour du mois concerné (ex: 01/01/2025)"
        self.fields['date_paiement'].help_text = "Date effective de réception du paiement"
        self.fields['date_echeance'].help_text = "Laissez vide pour le 5 du mois par défaut"
        self.fields['reference'].help_text = "Numéro de chèque, référence virement, etc."

        # Rendre certains champs non obligatoires
        self.fields['date_echeance'].required = False
        self.fields['reference'].required = False
        self.fields['autres'].required = False
        self.fields['notes'].required = False

        # Valeurs par défaut
        if not self.instance.pk:  # Si création (pas modification)
            self.fields['date_paiement'].initial = date.today()
            self.fields['valide'].initial = True
            self.fields['statut'].initial = 'recu'
            self.fields['autres'].initial = 0

        # Si un contrat_id est passé, filtrer les contrats actifs
        if contrat_id:
            self.fields['contrat'].initial = contrat_id
            self.fields['contrat'].widget.attrs['readonly'] = True

            # Pré-remplir avec les montants du contrat
            try:
                contrat = Contrats.objects.get(pk=contrat_id)
                if not self.instance.pk:
                    self.fields['loyer'].initial = contrat.loyer_mensuel
                    self.fields['charges'].initial = contrat.charges_mensuelles
            except Contrats.DoesNotExist:
                pass

        # Filtrer uniquement les contrats actifs dans le select
        self.fields['contrat'].queryset = Contrats.objects.filter(
            actif=True
        ).select_related('locataire', 'appartement__immeuble').order_by(
            'locataire__nom', 'locataire__prenom'
        )

        # Personnaliser l'affichage des contrats dans le select
        self.fields['contrat'].label_from_instance = lambda obj: (
            f"{obj.locataire.nom_complet} - "
            f"{obj.appartement.immeuble.nom} Apt {obj.appartement.numero}"
        )

    def clean_mois(self):
        """Validation du mois"""
        mois = self.cleaned_data.get('mois')

        if mois:
            # S'assurer que c'est le premier jour du mois
            mois = mois.replace(day=1)

            # Vérifier que ce n'est pas trop dans le futur
            if mois > date.today().replace(day=1):
                raise forms.ValidationError(
                    "Le mois ne peut pas être dans le futur."
                )

        return mois

    def clean_date_paiement(self):
        """Validation de la date de paiement"""
        date_paiement = self.cleaned_data.get('date_paiement')

        if date_paiement and date_paiement > date.today():
            raise forms.ValidationError(
                "La date de paiement ne peut pas être dans le futur."
            )

        return date_paiement

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()

        loyer = cleaned_data.get('loyer', 0)
        charges = cleaned_data.get('charges', 0)
        autres = cleaned_data.get('autres', 0)
        contrat = cleaned_data.get('contrat')
        mois = cleaned_data.get('mois')

        # Vérifier que le montant total est supérieur à 0
        total = loyer + charges + autres
        if total <= 0:
            raise forms.ValidationError(
                "Le montant total doit être supérieur à 0."
            )

        # Vérifier qu'il n'y a pas déjà un paiement pour ce mois
        if contrat and mois:
            existing = PaiementLocataire.objects.filter(
                contrat=contrat,
                mois=mois
            )

            # Exclure l'instance actuelle si c'est une modification
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    f"Un paiement existe déjà pour {mois.strftime('%B %Y')}. "
                    "Modifiez le paiement existant au lieu d'en créer un nouveau."
                )

        # Avertir si le montant est différent du contrat
        if contrat and loyer:
            montant_attendu = contrat.loyer_total
            montant_saisi = loyer + charges

            if abs(montant_saisi - montant_attendu) > 0.01:
                # Ajouter un warning (pas une erreur bloquante)
                self.add_warning(
                    'Le montant saisi ({:.2f}€) diffère du loyer du contrat ({:.2f}€)'.format(
                        montant_saisi, montant_attendu
                    )
                )

        return cleaned_data

    def add_warning(self, message):
        """Ajouter un avertissement (non bloquant)"""
        if not hasattr(self, '_warnings'):
            self._warnings = []
        self._warnings.append(message)

    def get_warnings(self):
        """Récupérer les avertissements"""
        return getattr(self, '_warnings', [])


# Formulaire simplifié pour enregistrement rapide
class PaiementRapideForm(forms.ModelForm):
    """Formulaire simplifié pour enregistrer rapidement un paiement"""

    class Meta:
        model = PaiementLocataire
        fields = ['mois', 'date_paiement', 'mode_paiement', 'reference']
        widgets = {
            'mois': DatePickerInput(
                format='%d/%m/%Y',
                options={
                    "locale": "fr",
                    "viewMode": "months",
                    "format": "MM/YYYY",
                }
            ),
            'date_paiement': DatePickerInput(
                format='%d/%m/%Y',
                options={
                    "locale": "fr",
                    "showTodayButton": True,
                }
            ),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence (optionnel)'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.contrat = kwargs.pop('contrat', None)
        super().__init__(*args, **kwargs)

        self.fields['date_paiement'].initial = date.today()
        self.fields['reference'].required = False

    def save(self, commit=True):
        paiement = super().save(commit=False)

        if self.contrat:
            paiement.contrat = self.contrat
            paiement.loyer = self.contrat.loyer_mensuel
            paiement.charges = self.contrat.charges_mensuelles
            paiement.statut = 'recu'
            paiement.valide = True

        if commit:
            paiement.save()

        return paiement


# Formulaire de recherche/filtrage
class PaiementSearchForm(forms.Form):
    """Formulaire de recherche des paiements"""

    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par locataire, appartement...'
        })
    )

    date_debut = forms.DateField(
        required=False,
        widget=DatePickerInput(
            format='%d/%m/%Y',
            options={"locale": "fr"}
        ),
        label="Du"
    )

    date_fin = forms.DateField(
        required=False,
        widget=DatePickerInput(
            format='%d/%m/%Y',
            options={"locale": "fr"}
        ),
        label="Au"
    )

    statut = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + PaiementLocataire._meta.get_field('statut').choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    mode_paiement = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les modes')] + PaiementLocataire._meta.get_field('mode_paiement').choices,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    en_retard = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Paiements en retard uniquement"
    )
