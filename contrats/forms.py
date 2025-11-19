from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .models import Contrats
from persons.models import Locataires
from immeuble.models import Appartement


class ContratForm(forms.ModelForm):
    class Meta:
        model = Contrats
        fields = [
            'locataire', 'appartement', 'date_debut', 'date_fin',
            'loyer_mensuel', 'charges_mensuelles', 'depot_garantie',
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

        # Rendre certains champs non obligatoires
        self.fields['date_fin'].required = False
        self.fields['indice_reference'].required = False
        self.fields['date_revision'].required = False
        self.fields['date_preavis'].required = False