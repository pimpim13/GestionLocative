# paiements/forms.py
from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .models import PaiementLocataire
from contrats.models import Contrats
from datetime import date
from calendar import monthrange


from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    TypeDepense,
    DepenseProprietaire,
    RepartitionDepense
)
from immeuble.models import Immeuble, Appartement


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
                options={
                    "format": 'DD-MM-YYYY',
                    "locale": "fr",
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            'date_echeance': DatePickerInput(
                options={
                    "format": 'DD-MM-YYYY',
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
        self.fields['date_echeance'].help_text = "Calculée automatiquement selon le contrat"
        self.fields['reference'].help_text = "Numéro de chèque, référence virement, etc."

        # Rendre certains champs non obligatoires
        self.fields['date_echeance'].required = False
        self.fields['reference'].required = False
        self.fields['autres'].required = False
        self.fields['notes'].required = False

        # Valeurs par défaut pour création
        if not self.instance.pk:  # Si création (pas modification)
            self.fields['date_paiement'].initial = date.today()
            self.fields['valide'].initial = True
            self.fields['statut'].initial = 'recu'
            self.fields['autres'].initial = 0

        # ============================================================
        # GESTION DU CONTRAT ET PRÉ-REMPLISSAGE
        # ============================================================
        if contrat_id:
            try:
                contrat = Contrats.objects.get(pk=contrat_id)

                # Pré-sélectionner le contrat et le rendre readonly
                self.fields['contrat'].initial = contrat_id
                self.fields['contrat'].widget.attrs['readonly'] = True

                # Pré-remplir les montants du contrat (uniquement en création)
                if not self.instance.pk:
                    self.fields['loyer'].initial = contrat.loyer_mensuel or 0
                    self.fields['charges'].initial = contrat.charges_mensuelles or 0

                    # ============================================================
                    # CALCUL AUTOMATIQUE DE LA DATE D'ÉCHÉANCE
                    # ============================================================
                    # Calculer pour le mois en cours par défaut
                    mois_actuel = date.today().replace(day=1)
                    jour_echeance = getattr(contrat, 'jour_echeance', 5)

                    # Vérifier que le jour d'échéance existe dans le mois
                    # (ex: éviter le 31 février)
                    _, dernier_jour = monthrange(mois_actuel.year, mois_actuel.month)
                    jour_echeance_valide = min(jour_echeance, dernier_jour)

                    # Définir la date d'échéance calculée
                    date_echeance_calculee = mois_actuel.replace(day=jour_echeance_valide)
                    self.fields['date_echeance'].initial = date_echeance_calculee

                    # Ajouter un attribut data pour JavaScript (optionnel)
                    self.fields['date_echeance'].widget.attrs['data-jour-echeance'] = jour_echeance

                    # Message d'aide personnalisé
                    self.fields['date_echeance'].help_text = (
                        f"Échéance contractuelle : le {jour_echeance} de chaque mois. "
                        f"Modifiable si nécessaire."
                    )

            except Contrats.DoesNotExist:
                pass

        # ✅ CORRECTION : Filtrer les contrats actifs avec prefetch_related au lieu de select_related
        self.fields['contrat'].queryset = Contrats.objects.filter(
            actif=True
        ).select_related(
            'appartement__immeuble'  # ✅ Garder select_related pour appartement
        ).prefetch_related(
            'locataires'  # ✅ Utiliser prefetch_related pour locataires (ManyToMany)
        ).order_by(
            'appartement__immeuble__nom',
            'appartement__numero'
        )

        # ✅ CORRECTION : Personnaliser l'affichage des contrats dans le select
        self.fields['contrat'].label_from_instance = lambda obj: (
            f"{obj.get_locataires_display()} - "
            f"{obj.appartement.immeuble.nom} Apt {obj.appartement.numero}"
        )

        # ============================================================
        # GESTION POUR MODIFICATION D'UN PAIEMENT EXISTANT
        # ============================================================
        if self.instance.pk and self.instance.contrat:
            # Recalculer l'échéance si elle n'est pas définie
            if not self.instance.date_echeance and self.instance.mois:
                contrat = self.instance.contrat
                jour_echeance = getattr(contrat, 'jour_echeance', 5)

                # Vérifier que le jour existe dans le mois du paiement
                _, dernier_jour = monthrange(
                    self.instance.mois.year,
                    self.instance.mois.month
                )
                jour_echeance_valide = min(jour_echeance, dernier_jour)

                self.fields['date_echeance'].initial = self.instance.mois.replace(
                    day=jour_echeance_valide
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

    def clean_date_echeance(self):
        """Validation et calcul automatique de la date d'échéance"""
        date_echeance = self.cleaned_data.get('date_echeance')
        mois = self.cleaned_data.get('mois')
        contrat = self.cleaned_data.get('contrat')

        # Si aucune échéance n'est fournie, la calculer
        if not date_echeance and mois and contrat:
            jour_echeance = getattr(contrat, 'jour_echeance', 5)

            # Vérifier que le jour existe dans le mois
            _, dernier_jour = monthrange(mois.year, mois.month)
            jour_echeance_valide = min(jour_echeance, dernier_jour)

            date_echeance = mois.replace(day=jour_echeance_valide)

        return date_echeance

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


class TypeDepenseForm(forms.ModelForm):
    """Formulaire pour créer/modifier un type de dépense"""

    class Meta:
        model = TypeDepense
        fields = [
            'nom', 'description', 'categorie',
            'recurrent', 'deductible_fiscalement', 'actif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Entretien ascenseur'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée (optionnel)'
            }),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'recurrent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'deductible_fiscalement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DepenseProprietaireForm(forms.ModelForm):
    """Formulaire pour créer/modifier une dépense propriétaire"""

    class Meta:
        model = DepenseProprietaire
        fields = [
            'immeuble', 'appartement', 'type_depense',
            'designation', 'description',
            'montant_ht', 'tva', 'montant_ttc',
            'date_depense', 'date_paiement', 'date_echeance',
            'fournisseur', 'fournisseur_siret',
            'numero_facture', 'mode_paiement', 'reference_paiement',
            'statut', 'repartissable', 'deductible_impots',
            'facture', 'justificatif', 'notes'
        ]
        widgets = {
            'immeuble': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_immeuble'
            }),
            'appartement': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_appartement'
            }),
            'type_depense': forms.Select(attrs={'class': 'form-select'}),
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Réparation chaudière'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée'
            }),
            'montant_ht': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'id': 'id_montant_ht'
            }),
            'tva': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'id': 'id_tva'
            }),
            'montant_ttc': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'id': 'id_montant_ttc',
                'readonly': True
            }),
            'date_depense': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_paiement': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_echeance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fournisseur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du fournisseur'
            }),
            'fournisseur_siret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '14 chiffres'
            }),
            'numero_facture': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° facture'
            }),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'reference_paiement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence'
            }),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'repartissable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'deductible_impots': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'facture': forms.FileInput(attrs={'class': 'form-control'}),
            'justificatif': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendre appartement optionnel et filtrer selon l'immeuble
        self.fields['appartement'].required = False

        # Si un immeuble est sélectionné, filtrer les appartements
        if 'immeuble' in self.data:
            try:
                immeuble_id = int(self.data.get('immeuble'))
                self.fields['appartement'].queryset = Appartement.objects.filter(
                    immeuble_id=immeuble_id
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.immeuble:
            self.fields['appartement'].queryset = Appartement.objects.filter(
                immeuble=self.instance.immeuble
            )

    def clean(self):
        cleaned_data = super().clean()
        montant_ht = cleaned_data.get('montant_ht')
        tva = cleaned_data.get('tva')
        montant_ttc = cleaned_data.get('montant_ttc')

        # Calculer automatiquement le TTC
        if montant_ht and tva is not None:
            calculated_ttc = montant_ht + tva
            cleaned_data['montant_ttc'] = calculated_ttc

        # Vérifier cohérence des montants
        if montant_ht and montant_ttc and tva is not None:
            if montant_ttc < montant_ht:
                raise ValidationError(
                    "Le montant TTC ne peut pas être inférieur au montant HT"
                )

        # Vérifier que l'appartement appartient à l'immeuble
        appartement = cleaned_data.get('appartement')
        immeuble = cleaned_data.get('immeuble')
        if appartement and immeuble:
            if appartement.immeuble != immeuble:
                raise ValidationError(
                    "L'appartement sélectionné n'appartient pas à cet immeuble"
                )

        return cleaned_data


class RepartitionDepenseForm(forms.ModelForm):
    """Formulaire pour répartir une dépense"""

    class Meta:
        model = RepartitionDepense
        fields = [
            'appartement', 'montant', 'mode_repartition',
            'base_calcul', 'coefficient', 'notes'
        ]
        widgets = {
            'appartement': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'id': 'id_montant_repartition'
            }),
            'mode_repartition': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_mode_repartition'
            }),
            'base_calcul': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'id': 'id_base_calcul'
            }),
            'coefficient': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, depense=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.depense = depense

        # Rendre base_calcul et coefficient optionnels
        self.fields['base_calcul'].required = False
        self.fields['coefficient'].required = False

        # Filtrer les appartements selon l'immeuble de la dépense
        if depense and depense.immeuble:
            # Exclure les appartements déjà dans une répartition
            appartements_deja_repartis = RepartitionDepense.objects.filter(
                depense=depense
            ).values_list('appartement_id', flat=True)

            # Récupérer les appartements qui ont un contrat actif
            from contrats.models import Contrats
            appartements_avec_contrat = Contrats.objects.filter(
                appartement__immeuble=depense.immeuble,
                actif=True
            ).values_list('appartement_id', flat=True).distinct()

            self.fields['appartement'].queryset = Appartement.objects.filter(
                immeuble=depense.immeuble,
                # id__in=appartements_avec_contrat
            ).exclude(
                id__in=appartements_deja_repartis
            )

    def clean(self):
        cleaned_data = super().clean()
        montant = cleaned_data.get('montant')

        # Vérifier que le montant ne dépasse pas le reste à répartir
        if self.depense and montant:
            repartitions_existantes = RepartitionDepense.objects.filter(
                depense=self.depense
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            total_deja_reparti = sum(r.montant for r in repartitions_existantes)
            reste_disponible = self.depense.montant_ttc - total_deja_reparti

            if montant > reste_disponible:
                raise ValidationError(
                    f"Le montant saisi ({montant}€) dépasse le reste à répartir ({reste_disponible}€)"
                )

        return cleaned_data


class RepartitionAutomatiqueForm(forms.Form):
    """Formulaire pour répartition automatique d'une dépense"""

    mode_repartition = forms.ChoiceField(
        label="Mode de répartition",
        choices=[
            ('surface', 'Par surface'),
            ('milliemes', 'Par millièmes'),
            ('egalitaire', 'Égalitaire'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    appartements = forms.ModelMultipleChoiceField(
        label="Appartements concernés",
        queryset=Appartement.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    tous_appartements = forms.BooleanField(
        label="Tous les appartements de l'immeuble",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, depense=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.depense = depense

        if depense and depense.immeuble:
            self.fields['appartements'].queryset = Appartement.objects.filter(
                immeuble=depense.immeuble
                # loue=True
            )


class FiltreDepensesForm(forms.Form):
    """Formulaire de filtrage des dépenses"""

    immeuble = forms.ModelChoiceField(
        queryset=Immeuble.objects.all(),
        required=False,
        empty_label="Tous les immeubles",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    type_depense = forms.ModelChoiceField(
        queryset=TypeDepense.objects.filter(actif=True),
        required=False,
        empty_label="Tous les types",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    categorie = forms.ChoiceField(
        choices=[('', 'Toutes les catégories')] + TypeDepense._meta.get_field('categorie').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + DepenseProprietaire._meta.get_field('statut').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    repartissable = forms.NullBooleanField(
        required=False,
        widget=forms.Select(
            choices=[
                ('', 'Toutes'),
                ('true', 'Répartissables uniquement'),
                ('false', 'Non répartissables uniquement')
            ],
            attrs={'class': 'form-select'}
        )
    )

    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...'
        })
    )