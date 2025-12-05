# paiements/models.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date

from accounts.models import TimeStampedModel


# =============================================================================
# MODÈLES POUR LES PAIEMENTS DES LOCATAIRES
# =============================================================================

class PaiementLocataire(TimeStampedModel):
    """Paiements des loyers par les locataires"""

    contrat = models.ForeignKey(
        'contrats.Contrats',
        on_delete=models.CASCADE,
        related_name='paiements_loyers'
    )

    # Période concernée
    mois = models.DateField(
        verbose_name="Mois concerné",
        help_text="Premier jour du mois concerné (ex: 01/01/2025)"
    )

    # Montants
    loyer = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Loyer payé",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    charges = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Charges payées",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    autres = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Autres montants (réparations, etc.)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Détails du paiement
    date_paiement = models.DateField(
        verbose_name="Date du paiement",
        help_text="Date effective de réception du paiement"
    )
    date_echeance = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'échéance",
        help_text="Date limite de paiement (généralement le 5 du mois)"
    )

    mode_paiement = models.CharField(
        max_length=50,
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('carte', 'Carte bancaire'),
            ('prelevement', 'Prélèvement automatique'),
        ],
        default='virement',
        verbose_name="Mode de paiement"
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Référence",
        help_text="Numéro de chèque, référence virement, etc."
    )

    # Statut et validation
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('recu', 'Reçu'),
            ('valide', 'Validé'),
            ('rejete', 'Rejeté'),
            ('partiel', 'Paiement partiel'),
        ],
        default='recu',
        verbose_name="Statut"
    )

    valide = models.BooleanField(
        default=True,
        verbose_name="Paiement validé"
    )

    # Quittance associée
    quittance = models.OneToOneField(
        'quittances.Quittance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiement_associe',
        verbose_name="Quittance générée"
    )

    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        ordering = ['-mois', '-date_paiement']
        verbose_name = "Paiement locataire"
        verbose_name_plural = "Paiements locataires"
        indexes = [
            models.Index(fields=['mois', 'contrat']),
            models.Index(fields=['date_paiement']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Paiement {self.contrat.locataire.nom_complet} - {self.mois.strftime('%m/%Y')}"

    @property
    def total(self):
        """Montant total du paiement"""
        return self.loyer + self.charges + self.autres

    @property
    def montant_attendu(self):
        """Montant attendu selon le contrat"""
        return self.contrat.loyer_total

    @property
    def en_retard(self):
        """Vérifie si le paiement est en retard"""
        if self.date_echeance:
            return self.date_paiement > self.date_echeance
        # Par défaut, échéance au 5 du mois
        echeance = self.mois.replace(day=5)
        return self.date_paiement > echeance

    @property
    def jours_retard(self):
        """Nombre de jours de retard"""
        if not self.en_retard:
            return 0
        echeance = self.date_echeance or self.mois.replace(day=5)
        return (self.date_paiement - echeance).days

    @property
    def est_complet(self):
        """Vérifie si le paiement est complet"""
        return self.total >= self.montant_attendu

    def save(self, *args, **kwargs):
        # Définir automatiquement la date d'échéance si non fournie
        if not self.date_echeance:
            self.date_echeance = self.mois.replace(day=self.contrat.jour_echeance)

        # Ajuster le statut selon le montant
        if self.total < self.montant_attendu:
            self.statut = 'partiel'

        super().save(*args, **kwargs)