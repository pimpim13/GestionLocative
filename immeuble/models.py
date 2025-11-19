#immeubles/models

from django.core.validators import MinValueValidator
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
    immeuble = models.ForeignKey(Immeuble, on_delete=models.CASCADE)
    numero = models.CharField(max_length=10)
    proprietaire = models.ForeignKey(Proprietaires, blank=True, null=True, on_delete=models.SET_NULL)
    etage = models.PositiveIntegerField()
    loue = models.BooleanField(default=False)

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

    def __str__(self):
        return f"{self.immeuble} - App : {self.numero}"


