from django.shortcuts import render, redirect
from django.http import HttpResponse

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import date, timedelta, datetime
from immeuble.models import Immeuble, Appartement
from persons.models import Locataires
from contrats.models import Contrats
from paiements.models import PaiementLocataire
from quittances.models import Quittance

def home(request):
    return render(request, 'home.html')


# @method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    """Tableau de bord principal"""
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistiques générales
        context.update({
            'total_immeubles': Immeuble.objects.count(),
            'total_appartements': Appartement.objects.count(),
            'appartements_loues': Appartement.objects.filter(loue=True).count(),
            'total_locataires': Locataires.objects.filter(actif=True).count(),
        })

        # Taux d'occupation
        if context['total_appartements'] > 0:
            context['taux_occupation'] = round(
                (context['appartements_loues'] / context['total_appartements']) * 100, 1
            )
        else:
            context['taux_occupation'] = 0

        # Revenus du mois
        mois_actuel = date.today().replace(day=1)
        revenus_mois = PaiementLocataire.objects.filter(
            mois=mois_actuel,
            valide=True
        ).aggregate(
            total=Sum('loyer'),
            charges=Sum('charges')
        )

        context['revenus_mois'] = {
            'loyers': revenus_mois['total'] or 0,
            'charges': revenus_mois['charges'] or 0,
            'total': (revenus_mois['total'] or 0) + (revenus_mois['charges'] or 0)
        }

        # Paiements en retard
        context['paiements_retard'] = self.get_paiements_retard()
        # Contrats se terminant bientôt
        context['contrats_fin_proche'] = self.get_contrats_fin_proche()

        # Activité récente
        context['activite_recente'] = self.get_activite_recente()

        # Graphiques de données
        context['graphique_revenus'] = self.get_graphique_revenus()
        # context['repartition_immeubles'] = self.get_repartition_immeubles()

        return context


    def get_paiements_retard(self):
        """Récupère les paiements en retard"""
        aujourd_hui = date.today()
        mois_actuel = aujourd_hui.replace(day=1)

        # Contrats actifs sans paiement pour le mois actuel
        contrats_sans_paiement = Contrats.objects.filter(
            actif=True,
            date_debut__lte=mois_actuel
        ).exclude(
            paiements_loyers__mois=mois_actuel
        ).select_related('locataire', 'appartement__immeuble'
        ).distinct()

        retards = []
        for contrat in contrats_sans_paiement:
            jours_retard = (aujourd_hui - mois_actuel.replace(day=5)).days
            if jours_retard > 0:
                retards.append({
                    'contrat': contrat,
                    'jours_retard': jours_retard,
                    'montant_du': contrat.loyer_total
                })

        return sorted(retards, key=lambda x: x['jours_retard'], reverse=True)[:5]




    def get_contrats_fin_proche(self):
        """Récupère les contrats se terminant bientôt"""
        dans_3_mois = date.today() + timedelta(days=90)

        return Contrats.objects.filter(
            actif=True,
            date_fin__lte=dans_3_mois,
            date_fin__gte=date.today()
        ).select_related('locataire', 'appartement__immeuble').order_by('date_fin')[:5]

    def get_activite_recente(self):
        """Récupère l'activité récente"""
        depuis_7_jours = timezone.now() - timedelta(days=7)

        activites = []

        # Paiements récents
        paiements_recents = PaiementLocataire.objects.filter(
            created_at__gte=depuis_7_jours
        ).select_related('contrat__locataire').order_by('-created_at')[:5]

        for paiement in paiements_recents:
            activites.append({
                'type': 'paiement',
                'date': paiement.created_at,
                'description': f'Enregistrement du paiement de {paiement.contrat.locataire.nom_complet} - {paiement.total}€',
                'objet': paiement
            })

        # Quittances générées
        quittances_recentes = Quittance.objects.filter(
            created_at__gte=depuis_7_jours
        ).select_related('contrat__locataire').order_by('-created_at')[:5]

        for quittance in quittances_recentes:
            activites.append({
                'type': 'quittance',
                'date': quittance.created_at,
                'description': f'Quittance {quittance.numero} générée pour {quittance.contrat.locataire.nom_complet}',
                'objet': quittance
            })

        return sorted(activites, key=lambda x: x['date'], reverse=True)[:10]

    def get_graphique_revenus(self):
        """Données pour le graphique des revenus des 12 derniers mois"""
        aujourd_hui = date.today()
        donnees = []

        for i in range(12):
            mois = aujourd_hui.replace(day=1) - timedelta(days=30 * i)
            revenus = PaiementLocataire.objects.filter(
                mois__year=mois.year,
                mois__month=mois.month,
                valide=True
            ).aggregate(
                total=Sum('loyer'),
                charges=Sum('charges')
            )

            donnees.append({
                'mois': mois.strftime('%b %Y'),
                'loyers': float(revenus['total'] or 0),
                'charges': float(revenus['charges'] or 0)
            })

        return list(reversed(donnees))

    def get_repartition_immeubles(self):
        """Répartition des appartements par immeuble"""
        return Immeuble.objects.filter(actif=True).annotate(
            nb_appartements=Count('appartements'),
            nb_loues=Count('appartements', filter=Q(appartements__loue=True))
        ).values('nom', 'nb_appartements', 'nb_loues')