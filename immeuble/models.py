#immeubles/models.py

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from accounts.models import TimeStampedModel
from persons.models import Proprietaires
from accounts.models import CustomUser



class Immeuble(TimeStampedModel):
    nom = models.CharField(max_length=200)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)
    charges_communes_annuelles = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Charges communes annuelles"
    )

    def __str__(self):
        return self.nom


class Appartement(TimeStampedModel):
    immeuble = models.ForeignKey(Immeuble, related_name='appartements', on_delete=models.CASCADE)
    numero = models.CharField(max_length=10)
    proprietaire = models.ForeignKey(Proprietaires, blank=True, null=True, on_delete=models.SET_NULL)
    etage = models.PositiveIntegerField()
    # loue = models.BooleanField(default=False)

    # Financier
    loyer_base = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(100.00)],
        verbose_name="Loyer de base",
        null=True,
        blank=True,
    )
    charges_mensuelles = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Charges mensuelles",
        null=True,
        blank=True,
    )

    surface = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Surface (m²)"
    )

    milliemes = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Millièmes",
        validators=[
            MinValueValidator(0),
            MaxValueValidator(999),
        ]
    )

    @property
    def contrats_actifs(self):
        """Retourne les contrats actifs pour cet appartement"""
        from contrats.models import Contrats
        return Contrats.objects.filter(
            appartement=self,
            actif=True
        ).select_related('appartement').prefetch_related('locataires')

    @property
    def contrat_actif(self):
        """Retourne le premier contrat actif (le plus récent)"""
        return self.contrats_actifs.order_by('-date_debut').first()

    @property
    def locataire_actuel(self):
        """Retourne le locataire principal du contrat actif"""
        contrat = self.contrat_actif
        if contrat:
            return contrat.get_locataire_principal()
        return None

    @property
    def loue(self):
        """Vérifie si l'appartement a un contrat actif"""
        return self.contrats_actifs.exists()

    def __str__(self):
        return f"{self.immeuble} - App : {self.numero}"


