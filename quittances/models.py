# quittances/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Max
from decimal import Decimal
from datetime import date
from accounts.models import TimeStampedModel


def quittance_upload_path(instance, filename):
    # instance.dt est un objet date
    year = instance.mois.year
    month = instance.mois.month

    # Exemple : 'quittances/2025/03/monfichier.pdf'
    return f"quittances/{year}/{month:02d}/{filename}"


class Quittance(TimeStampedModel):
    """Modèle pour les quittances de loyer"""

    contrat = models.ForeignKey(
        'contrats.Contrats',
        on_delete=models.CASCADE,
        related_name='quittances'
    )

    # Période et numérotation
    mois = models.DateField(verbose_name="Mois concerné")
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de quittance"
    )

    # Montants (copiés depuis le paiement ou le contrat)
    loyer = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Loyer hors charges"
    )
    charges = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Charges"
    )
    total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Total"
    )

    # Dates importantes
    date_generation = models.DateTimeField(auto_now_add=True)
    date_envoi = models.DateTimeField(null=True, blank=True)

    # Fichiers
    fichier_pdf = models.FileField(
        upload_to=quittance_upload_path,
        blank=True,
        verbose_name="Fichier PDF"
    )

    # Statuts
    envoyee = models.BooleanField(default=False, verbose_name="Envoyée")
    mode_envoi = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('courrier', 'Courrier postal'),
            ('remise_main', 'Remise en main propre'),
            ('portail', 'Téléchargée sur portail'),
        ],
        blank=True
    )

    # Lien avec le paiement (optionnel)
    paiement = models.OneToOneField(
        'paiements.PaiementLocataire',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quittance_generee',
        verbose_name="Paiement associé"
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-mois', '-date_generation']
        unique_together = ['contrat', 'mois']
        verbose_name = "Quittance"
        verbose_name_plural = "Quittances"
        indexes = [
            models.Index(fields=['mois', 'contrat']),
            models.Index(fields=['numero']),
            models.Index(fields=['envoyee']),
        ]

    def __str__(self):
        # ✅ CORRECTION : utiliser get_locataire_principal()
        locataire = self.contrat.get_locataire_principal()
        nom = locataire.nom_complet if locataire else "Sans locataire"
        return f"Quittance {self.numero} - {nom}"

    def save(self, *args, **kwargs):
        # Génération automatique du numéro si non fourni
        if not self.numero:
            year = self.mois.year
            month = self.mois.month

            # ✅ CORRECTION : Utiliser le numéro maximum existant + 1
            # au lieu de count() pour éviter les doublons
            prefix = f"Q{year}{month:02d}"

            # Récupérer le dernier numéro pour ce mois
            last_quittance = Quittance.objects.filter(
                numero__startswith=prefix
            ).aggregate(Max('numero'))

            last_numero = last_quittance['numero__max']

            if last_numero:
                # Extraire le compteur du dernier numéro (les 4 derniers chiffres)
                try:
                    last_count = int(last_numero[-4:])
                    next_count = last_count + 1
                except (ValueError, IndexError):
                    # Si l'extraction échoue, recommencer à 1
                    next_count = 1
            else:
                # Aucune quittance pour ce mois, commencer à 1
                next_count = 1

            self.numero = f"{prefix}{next_count:04d}"

        # Calcul automatique du total si non fourni
        if not self.total:
            self.total = self.loyer + self.charges

        super().save(*args, **kwargs)

    @property
    def locataire_principal(self):
        """Raccourci vers le locataire principal"""
        return self.contrat.get_locataire_principal()

    @property
    def tous_locataires(self):
        """Raccourci vers tous les locataires"""
        return self.contrat.get_tous_locataires()

    @property
    def appartement(self):
        """Raccourci vers l'appartement"""
        return self.contrat.appartement

    @property
    def immeuble(self):
        """Raccourci vers l'immeuble"""
        return self.contrat.appartement.immeuble