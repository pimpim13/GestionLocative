# quittances/utils.py
from decimal import Decimal

from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Quittance
from .pdf_generator import QuittancePDFGenerator
from datetime import date
import calendar


class QuittanceManager:
    """Gestionnaire pour la création et gestion des quittances"""

    @staticmethod
    def generer_quittance(contrat, mois, paiement=None, force_regeneration=False):
        """
        Génère une quittance pour un contrat et un mois donné

        Args:
            contrat: Instance du modèle Contrats
            mois: Date du premier jour du mois (datetime.date)
            paiement: Instance de PaiementLocataire (optionnel)
            force_regeneration: Force la régénération si la quittance existe déjà

        Returns:
            Quittance: Instance de la quittance générée
        """
        # Vérifier si une quittance existe déjà
        quittance_existante = Quittance.objects.filter(
            contrat=contrat,
            mois=mois
        ).first()

        if quittance_existante and not force_regeneration:
            return quittance_existante

        # Déterminer les montants
        if paiement:
            # Utiliser les montants du paiement
            loyer = paiement.loyer
            charges = paiement.charges
        elif quittance_existante:
            # Conserver les montants existants
            loyer = quittance_existante.loyer
            charges = quittance_existante.charges
        else:
            # Utiliser les montants du contrat
            loyer = contrat.loyer_mensuel or Decimal('0')
            charges = contrat.charges_mensuelles or Decimal('0')

        # Créer ou mettre à jour la quittance
        if quittance_existante:
            quittance = quittance_existante
            quittance.loyer = loyer
            quittance.charges = charges
            quittance.total = loyer + charges
            if paiement:
                quittance.paiement = paiement
        else:
            quittance = Quittance.objects.create(
                contrat=contrat,
                mois=mois,
                loyer=loyer,
                charges=charges,
                total=loyer + charges,
                paiement=paiement
            )

        # Générer le PDF
        try:
            pdf_generator = QuittancePDFGenerator(quittance)
            pdf_content = pdf_generator.generate_pdf()

            # Sauvegarder le fichier PDF
            filename = f"quittance_{quittance.numero}_{mois.strftime('%Y%m')}.pdf"
            quittance.fichier_pdf.save(
                filename,
                ContentFile(pdf_content),
                save=True
            )
        except Exception as e:
            print(f"Erreur lors de la génération du PDF: {e}")
            # Sauvegarder la quittance même si le PDF échoue
            quittance.save()

        return quittance

    @staticmethod
    def generer_quittances_batch(contrats, mois):
        """
        Génère les quittances pour plusieurs contrats en lot

        Args:
            contrats: QuerySet ou liste de contrats
            mois: Date du premier jour du mois

        Returns:
            dict: Résultat avec liste des quittances et statistiques
        """
        quittances_generees = []
        erreurs = []

        for contrat in contrats:
            try:
                quittance = QuittanceManager.generer_quittance(contrat, mois)
                quittances_generees.append(quittance)
            except Exception as e:
                erreurs.append({
                    'contrat': contrat,
                    'erreur': str(e)
                })

        return {
            'success': len(quittances_generees),
            'errors': len(erreurs),
            'quittances': quittances_generees,
            'erreurs_detail': erreurs
        }

    @staticmethod
    def generer_quittances_mois(mois, immeubles=None):
        """
        Génère toutes les quittances pour un mois donné

        Args:
            mois: Date du premier jour du mois
            immeubles: Liste d'immeubles (optionnel, sinon tous)

        Returns:
            dict: Résultat de la génération avec statistiques
        """
        from contrats.models import Contrats
        from django.db.models import Q

        # Récupérer les contrats actifs pour ce mois
        contrats_query = Contrats.objects.filter(
            actif=True,
            date_debut__lte=mois
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=mois)
        )

        # Filtrer par immeubles si spécifié
        if immeubles:
            contrats_query = contrats_query.filter(
                appartement__immeuble__in=immeubles
            )

        contrats = contrats_query.select_related(
            'locataire',
            'appartement',
            'appartement__immeuble'
        )

        # Générer les quittances
        resultats = QuittanceManager.generer_quittances_batch(contrats, mois)

        return {
            'total_contrats': contrats.count(),
            'quittances_generees': resultats['success'],
            'erreurs': resultats['errors'],
            'quittances': resultats['quittances'],
            'erreurs_detail': resultats['erreurs_detail'],
            'mois': mois
        }

    @staticmethod
    def generer_depuis_paiement(paiement):
        """
        Génère une quittance à partir d'un paiement

        Args:
            paiement: Instance de PaiementLocataire

        Returns:
            Quittance: Quittance générée
        """
        return QuittanceManager.generer_quittance(
            contrat=paiement.contrat,
            mois=paiement.mois,
            paiement=paiement,
            force_regeneration=False
        )