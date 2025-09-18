from django.db import models


class TimeStampedModel(models.Model):
    """Modèle abstrait pour horodatage automatique"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    created_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name="Créé par"
    )

    class Meta:
        abstract = True