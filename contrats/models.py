# contrats/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import TimeStampedModel
from persons.models import Locataires
from immeuble.models import Appartement


class Contrats(TimeStampedModel):
    """Modèle pour les contrats de bail"""

    # ✅ RELATION ManyToMany (système simplifié)
    locataires = models.ManyToManyField(
        Locataires,
        through='ContratLocataire',
        related_name='contrats',
        verbose_name="Locataires du bail"
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
        null=True,
        blank=True
    )
    charges_mensuelles = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Charges mensuelles",
        null=True,
        blank=True
    )
    jour_echeance = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="Jour d'échéance"
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
        locataires_noms = self.get_locataires_display()
        return f"Contrat {locataires_noms} - {self.appartement}"

    @property
    def loyer_total(self):
        """Loyer total charges comprises"""
        return (self.loyer_mensuel or 0) + (self.charges_mensuelles or 0)

    @property
    def duree_mois(self):
        """Durée du contrat en mois"""
        if self.date_fin:
            delta = self.date_fin - self.date_debut
            return delta.days // 30
        return None

    # ============================================================
    # MÉTHODES POUR GÉRER LES LOCATAIRES MULTIPLES
    # ============================================================

    def get_locataire_principal(self):
        """Retourne le locataire principal (contact)"""
        relation = self.contratlocataire_set.filter(
            principal=True,
            date_sortie__isnull=True
        ).first()

        if relation:
            return relation.locataire

        # Fallback : premier locataire par ordre
        relation = self.contratlocataire_set.filter(
            date_sortie__isnull=True
        ).order_by('ordre').first()

        return relation.locataire if relation else None

    def get_tous_locataires(self):
        """Retourne tous les locataires actifs du contrat"""
        return self.locataires.filter(
            contratlocataire__date_sortie__isnull=True
        ).order_by('contratlocataire__ordre')

    def get_locataires_display(self, separator=" et "):
        """Affichage formaté des locataires pour les documents"""
        locataires = list(self.get_tous_locataires())  # Convertir en liste

        if len(locataires) == 0:
            return "Aucun locataire"
        elif len(locataires) == 1:
            return locataires[0].nom_complet
        elif len(locataires) == 2:
            return f"{locataires[0].nom_complet} et {locataires[1].nom_complet}"
        else:
            noms = [loc.nom_complet for loc in locataires[:-1]]
            return f"{', '.join(noms)} et {locataires[-1].nom_complet}"

    def get_locataires_quittance(self):
        """Format spécial pour quittance (chaque nom sur une ligne)"""
        locataires = list(self.get_tous_locataires())  # ⬅️ Conversion en liste
        return "\n".join([loc.nom_complet for loc in locataires])

    def ajouter_locataire(self, locataire, principal=False, role='cotitulaire', ordre=None):
        """Ajoute un locataire au contrat"""
        if ordre is None:
            # Calculer le prochain ordre
            max_ordre = self.contratlocataire_set.aggregate(
                models.Max('ordre')
            )['ordre__max'] or 0
            ordre = max_ordre + 1

        ContratLocataire.objects.create(
            contrat=self,
            locataire=locataire,
            principal=principal,
            date_entree=self.date_debut,
            ordre=ordre,
            role=role
        )

    def retirer_locataire(self, locataire, date_sortie):
        """Marque un locataire comme sorti du bail"""
        ContratLocataire.objects.filter(
            contrat=self,
            locataire=locataire
        ).update(date_sortie=date_sortie)


class ContratLocataire(TimeStampedModel):
    """Table intermédiaire pour gérer plusieurs locataires par contrat"""

    contrat = models.ForeignKey(
        Contrats,
        on_delete=models.CASCADE,
        verbose_name="Contrat"
    )
    locataire = models.ForeignKey(
        Locataires,
        on_delete=models.PROTECT,
        verbose_name="Locataire"
    )

    # Métadonnées
    principal = models.BooleanField(
        default=False,
        verbose_name="Contact principal",
        help_text="Locataire à contacter en priorité"
    )
    ordre = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Ordre d'affichage",
        help_text="Ordre d'apparition sur les documents (1, 2, 3...)"
    )

    # Dates de présence sur le bail
    date_entree = models.DateField(
        verbose_name="Date d'entrée dans le bail",
        help_text="Date à laquelle ce locataire a rejoint le bail"
    )
    date_sortie = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de sortie du bail",
        help_text="Laisser vide si toujours sur le bail"
    )

    # Informations complémentaires
    role = models.CharField(
        max_length=50,
        choices=[
            ('titulaire', 'Titulaire'),
            ('cotitulaire', 'Co-titulaire'),
            ('garant', 'Garant'),
        ],
        default='cotitulaire',
        verbose_name="Rôle"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Notes spécifiques à cette relation locataire-contrat"
    )

    class Meta:
        unique_together = ['contrat', 'locataire']
        ordering = ['ordre', 'date_entree']
        verbose_name = "Locataire du contrat"
        verbose_name_plural = "Locataires du contrat"
        indexes = [
            models.Index(fields=['contrat', 'principal']),
            models.Index(fields=['locataire', 'date_sortie']),
        ]

    def __str__(self):
        status = "Principal" if self.principal else "Secondaire"
        actif = "Actif" if not self.date_sortie else f"Sorti le {self.date_sortie}"
        return f"{self.locataire.nom_complet} - {self.contrat} ({status}, {actif})"

    @property
    def est_actif(self):
        """Vérifie si le locataire est toujours sur le bail"""
        return self.date_sortie is None

    def save(self, *args, **kwargs):
        # Si marqué comme principal, retirer le flag des autres
        if self.principal:
            ContratLocataire.objects.filter(
                contrat=self.contrat,
                principal=True
            ).exclude(pk=self.pk).update(principal=False)

        # Définir date_entree par défaut
        if not self.date_entree:
            self.date_entree = self.contrat.date_debut

        super().save(*args, **kwargs)