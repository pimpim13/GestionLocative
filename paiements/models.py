# paiements/models.py
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date

from accounts.models import TimeStampedModel
from contrats.models import Contrats

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

    loyer_attendu = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Loyer payé",
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,
        blank=True


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
        # ✅ CORRECTION : utiliser get_locataire_principal()
        locataire = self.contrat.get_locataire_principal()
        nom = locataire.nom_complet if locataire else "Sans locataire"
        return f"Paiement {nom} - {self.mois.strftime('%m/%Y')}"

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

        if not self.loyer_attendu:
            loyer = Contrats.objects.get(id=self.contrat.id).loyer_mensuel
            self.loyer_attendu = loyer

        # Ajuster le statut selon le montant
        if self.total < self.montant_attendu:
            self.statut = 'partiel'

        super().save(*args, **kwargs)


# =============================================================================
# MODÈLES POUR LES DÉPENSES DES PROPRIÉTAIRES
# =============================================================================

class TypeDepense(models.Model):
    """Types de dépenses pour les propriétaires"""

    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    categorie = models.CharField(
        max_length=50,
        choices=[
            ('entretien', 'Entretien et réparations'),
            ('charges', 'Charges d\'immeuble'),
            ('travaux', 'Travaux et rénovations'),
            ('assurance', 'Assurances'),
            ('taxe', 'Taxes et impôts'),
            ('honoraires', 'Honoraires professionnels'),
            ('fourniture', 'Fournitures et équipements'),
            ('autre', 'Autre'),
        ],
        default='charges'
    )

    recurrent = models.BooleanField(
        default=False,
        verbose_name="Dépense récurrente"
    )

    deductible_fiscalement = models.BooleanField(
        default=True,
        verbose_name="Déductible fiscalement"
    )

    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['categorie', 'nom']
        verbose_name = "Type de dépense"
        verbose_name_plural = "Types de dépenses"

    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"


class DepenseProprietaire(TimeStampedModel):
    """Dépenses et charges payées par le propriétaire"""

    # Immeuble concerné (peut être null pour dépenses globales)
    immeuble = models.ForeignKey(
        'immeuble.Immeuble',
        on_delete=models.CASCADE,
        related_name='depenses',
        null=True,
        blank=True,
        verbose_name="Immeuble"
    )

    # Appartement concerné (optionnel, pour dépenses spécifiques)
    appartement = models.ForeignKey(
        'immeuble.Appartement',
        on_delete=models.CASCADE,
        related_name='depenses',
        null=True,
        blank=True,
        verbose_name="Appartement"
    )

    # Type de dépense
    type_depense = models.ForeignKey(
        TypeDepense,
        on_delete=models.PROTECT,
        related_name='depenses'
    )

    # Description
    designation = models.CharField(
        max_length=200,
        verbose_name="Désignation"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description détaillée"
    )

    # Montants
    montant_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant HT",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    tva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="TVA",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    montant_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant TTC",
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Dates
    date_depense = models.DateField(
        verbose_name="Date de la dépense",
        help_text="Date de la facture ou du service"
    )
    date_paiement = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de paiement"
    )
    date_echeance = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'échéance"
    )

    # Fournisseur
    fournisseur = models.CharField(
        max_length=200,
        verbose_name="Fournisseur/Prestataire"
    )
    fournisseur_siret = models.CharField(
        max_length=14,
        blank=True,
        verbose_name="SIRET du fournisseur"
    )

    # Référence et paiement
    numero_facture = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro de facture"
    )
    mode_paiement = models.CharField(
        max_length=50,
        choices=[
            ('virement', 'Virement'),
            ('cheque', 'Chèque'),
            ('carte', 'Carte bancaire'),
            ('prelevement', 'Prélèvement'),
            ('especes', 'Espèces'),
        ],
        default='virement'
    )
    reference_paiement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Référence de paiement"
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=[
            ('a_payer', 'À payer'),
            ('payee', 'Payée'),
            ('en_attente', 'En attente de validation'),
            ('annulee', 'Annulée'),
        ],
        default='a_payer'
    )

    # Caractéristiques
    repartissable = models.BooleanField(
        default=False,
        verbose_name="Répartissable sur locataires",
        help_text="Cette charge peut être répartie entre les locataires"
    )

    repartie = models.BooleanField(
        default=False,
        verbose_name="Déjà répartie"
    )

    deductible_impots = models.BooleanField(
        default=True,
        verbose_name="Déductible des impôts"
    )

    # Documents
    facture = models.FileField(
        upload_to='depenses/factures/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Facture"
    )
    justificatif = models.FileField(
        upload_to='depenses/justificatifs/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Justificatif"
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_depense']
        verbose_name = "Dépense propriétaire"
        verbose_name_plural = "Dépenses propriétaires"
        indexes = [
            models.Index(fields=['date_depense']),
            models.Index(fields=['statut']),
            models.Index(fields=['immeuble', 'date_depense']),
        ]

    def __str__(self):
        immeuble_str = f" - {self.immeuble.nom}" if self.immeuble else ""
        return f"{self.designation}{immeuble_str} - {self.montant_ttc}€"

    @property
    def est_payee(self):
        """Vérifie si la dépense est payée"""
        return self.statut == 'payee' and self.date_paiement is not None

    @property
    def est_en_retard(self):
        """Vérifie si le paiement est en retard"""
        if self.statut == 'payee' or not self.date_echeance:
            return False
        return date.today() > self.date_echeance

    @property
    def jours_retard(self):
        """Nombre de jours de retard"""
        if not self.est_en_retard:
            return 0
        return (date.today() - self.date_echeance).days

    def save(self, *args, **kwargs):
        # Calculer automatiquement le TTC si non fourni
        if not self.montant_ttc or self.montant_ttc == 0:
            self.montant_ttc = self.montant_ht + self.tva

        # Si payée, s'assurer qu'il y a une date de paiement
        if self.statut == 'payee' and not self.date_paiement:
            self.date_paiement = date.today()

        super().save(*args, **kwargs)


class RepartitionDepense(TimeStampedModel):
    """Répartition d'une dépense entre plusieurs appartements/locataires"""

    depense = models.ForeignKey(
        DepenseProprietaire,
        on_delete=models.CASCADE,
        related_name='repartitions'
    )

    appartement = models.ForeignKey(
        'immeuble.Appartement',
        on_delete=models.CASCADE,
        related_name='repartitions_charges'
    )

    # Montant réparti pour cet appartement
    montant = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    # Base de calcul de la répartition
    mode_repartition = models.CharField(
        max_length=20,
        choices=[
            ('surface', 'Par surface'),
            ('tantieme', 'Par tantièmes'),
            ('forfait', 'Forfait'),
            ('personnalise', 'Personnalisé'),
        ],
        default='surface'
    )

    base_calcul = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Surface, tantièmes, ou autre base de calcul"
    )

    coefficient = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Coefficient appliqué pour le calcul"
    )

    # Statut
    facturee_locataire = models.BooleanField(
        default=False,
        verbose_name="Facturée au locataire"
    )

    date_facturation = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de facturation"
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['depense', 'appartement']
        unique_together = ['depense', 'appartement']
        verbose_name = "Répartition de dépense"
        verbose_name_plural = "Répartitions de dépenses"

    def __str__(self):
        return f"{self.depense.designation} - {self.appartement} : {self.montant}€"


# =============================================================================
# MODÈLE POUR LES RAPPELS DE PAIEMENT
# =============================================================================

class RappelPaiement(TimeStampedModel):
    """Rappels et relances pour paiements en retard"""

    paiement_locataire = models.ForeignKey(
        PaiementLocataire,
        on_delete=models.CASCADE,
        related_name='rappels',
        null=True,
        blank=True
    )

    contrat = models.ForeignKey(
        'contrats.Contrats',
        on_delete=models.CASCADE,
        related_name='rappels'
    )

    # Type de rappel
    type_rappel = models.CharField(
        max_length=20,
        choices=[
            ('premier', 'Premier rappel'),
            ('deuxieme', 'Deuxième rappel'),
            ('mise_demeure', 'Mise en demeure'),
            ('contentieux', 'Contentieux'),
        ],
        default='premier'
    )

    # Dates
    date_envoi = models.DateField(
        verbose_name="Date d'envoi du rappel"
    )
    date_limite_reponse = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date limite de réponse"
    )

    # Montants
    montant_du = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Montant dû"
    )
    penalites = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Pénalités de retard"
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=[
            ('envoye', 'Envoyé'),
            ('regle', 'Réglé'),
            ('sans_reponse', 'Sans réponse'),
            ('contentieux', 'En contentieux'),
        ],
        default='envoye'
    )

    # Méthode d'envoi
    mode_envoi = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('courrier', 'Courrier simple'),
            ('recommande', 'Courrier recommandé'),
            ('huissier', 'Par huissier'),
        ],
        default='email'
    )

    # Document
    document = models.FileField(
        upload_to='rappels/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Document de rappel"
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_envoi']
        verbose_name = "Rappel de paiement"
        verbose_name_plural = "Rappels de paiement"

    def __str__(self):
        return f"{self.get_type_rappel_display()} - {self.contrat.locataire.nom_complet} - {self.date_envoi}"

    @property
    def total_du(self):
        """Montant total dû avec pénalités"""
        return self.montant_du + self.penalites


# =============================================================================
# MODÈLE POUR LES STATISTIQUES ET RAPPORTS
# =============================================================================

class RapportFinancier(TimeStampedModel):
    """Rapports financiers périodiques"""

    # Période
    periode_debut = models.DateField(verbose_name="Début de période")
    periode_fin = models.DateField(verbose_name="Fin de période")

    # Type de rapport
    type_rapport = models.CharField(
        max_length=20,
        choices=[
            ('mensuel', 'Mensuel'),
            ('trimestriel', 'Trimestriel'),
            ('annuel', 'Annuel'),
            ('personnalise', 'Personnalisé'),
        ],
        default='mensuel'
    )

    # Immeuble concerné (null = tous les immeubles)
    immeuble = models.ForeignKey(
        'immeuble.Immeuble',
        on_delete=models.CASCADE,
        related_name='rapports_financiers',
        null=True,
        blank=True
    )

    # Revenus
    total_loyers_percus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_charges_percues = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Dépenses
    total_depenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Résultat
    resultat_net = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Revenus - Dépenses"
    )

    # Taux d'occupation
    taux_occupation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Pourcentage d'occupation"
    )

    # Impayés
    total_impayes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Document généré
    fichier_rapport = models.FileField(
        upload_to='rapports/%Y/%m/',
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-periode_debut']
        unique_together = ['periode_debut', 'periode_fin', 'immeuble']
        verbose_name = "Rapport financier"
        verbose_name_plural = "Rapports financiers"

    def __str__(self):
        immeuble_str = f" - {self.immeuble.nom}" if self.immeuble else " - Tous"
        return f"Rapport {self.get_type_rapport_display()}{immeuble_str} ({self.periode_debut} - {self.periode_fin})"

    @property
    def rentabilite(self):
        """Calcule la rentabilité en pourcentage"""
        if self.total_depenses == 0:
            return 100
        return (self.resultat_net / (self.total_loyers_percus + self.total_charges_percues) * 100).quantize(
            Decimal('0.01'))