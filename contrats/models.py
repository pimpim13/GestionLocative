#contrats/models.py

from django.db import models
from accounts.models import TimeStampedModel
from persons.models import Locataires
from immeuble.models import Appartement
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator


class Contrats(TimeStampedModel):
    """Modèle pour les contrats de bail"""
    locataire = models.ForeignKey(
        Locataires,
        on_delete=models.CASCADE,
        related_name='contrats'
    )
    appartement = models.ForeignKey(
        Appartement,
        on_delete=models.CASCADE,
        related_name='contrats'
    )

    # Dates du contrat
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin prévue"
    )
    date_fin_effective = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin effective"
    )

    # Conditions financières
    loyer_mensuel = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Loyer mensuel hors charges",
        null = True,
        blank = True
    )

    charges_mensuelles = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Charges mensuelles",
        null = True,
        blank = True
    )

    jour_echeance = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Jour d'échéance",
        help_text = "Jour du mois où le loyer doit être payé"
    )

    depot_garantie = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Dépôt de garantie",
        null=True,
        blank=True
    )

    # Révision du loyer
    indice_reference = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Indice de référence IRL"
    )
    date_revision = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de révision annuelle"
    )

    # État du contrat
    actif = models.BooleanField(default=True)
    preavis_donne = models.BooleanField(default=False, verbose_name="Préavis donné")
    date_preavis = models.DateField(null=True, blank=True)

    # Documents
    fichier_contrat = models.FileField(
        upload_to='contrats/',
        null=True,
        blank=True,
        verbose_name="Fichier du contrat"
    )
    etat_lieux_entree = models.FileField(
        upload_to='etats_lieux/',
        null=True,
        blank=True,
        verbose_name="État des lieux d'entrée"
    )
    etat_lieux_sortie = models.FileField(
        upload_to='etats_lieux/',
        null=True,
        blank=True,
        verbose_name="État des lieux de sortie"
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_debut']
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"

    def __str__(self):
        return f"Contrat {self.locataire} - {self.appartement}"

    @property
    def loyer_total(self):
        return self.loyer_mensuel + self.charges_mensuelles

    @property
    def duree_mois(self):
        if self.date_fin:
            delta = self.date_fin - self.date_debut
            return delta.days // 30
        return None