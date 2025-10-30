from django.db import models

class Appt(models.Model):
    nom = models.CharField(max_length=10)
    loyer = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,)

class Pay(models.Model):
    num=models.CharField(max_length=10)
    loyer = models.ForeignKey(Appt , on_delete=models.DO_NOTHING)

