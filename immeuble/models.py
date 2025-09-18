from django.db import models
from accounts.models import TimeStampedModel


class Immeuble(TimeStampedModel):
    nom = models.CharField(max_length=200)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)

    def __str__(self):
        return self.nom


class Appartement(TimeStampedModel):
    immeuble = models.ForeignKey(Immeuble, on_delete=models.CASCADE)
    numero = models.CharField(max_length=10)
    etage = models.PositiveIntegerField()
    loue = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.immeuble} - App : {self.numero}"
