#persons/models.py

from django.core.validators import RegexValidator
from django.db import models

from accounts.models import TimeStampedModel

class Proprietaires(TimeStampedModel):
    raison_sociale = models.CharField(max_length=50, blank=True, verbose_name='Raison Sociale')
    nom = models.CharField(max_length=50, default='inconnu')
    prenom = models.CharField(max_length=50, default='inconnu')
    email = models.EmailField(unique=True)
    telephone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?[\d\s\-\(\)]+$', 'Format de téléphone invalide')])
    actif = models.BooleanField(default=True)

    def __str__(self):
        if self.raison_sociale:
            return f'{self.raison_sociale}'
        else:
            return f'{self.nom} {self.prenom}'


class Locataires(TimeStampedModel):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    email = models.EmailField(unique=True)
    telephone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?[\d\s\-\(\)]+$', 'Format de téléphone invalide')]
    )
    notes = models.TextField(blank=True)
    actif = models.BooleanField(default=True)


    class Meta:
        ordering = ['nom', 'prenom']
        verbose_name = "Locataire"
        verbose_name_plural = "Locataires"

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"



