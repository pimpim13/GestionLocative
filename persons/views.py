# persons/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.contrib import messages

from persons.models import Proprietaires, Locataires
from persons.forms import ProprietaireForm, LocataireForm
from contrats.models import Contrats, ContratLocataire
from paiements.models import PaiementLocataire
from quittances.models import Quittance


def persons_accueil(request):
    return render(request, "persons/persons_accueil.html")


# ============================================================
# VUES POUR LES PROPRIÉTAIRES
# ============================================================

class Proprietaires_ListView(ListView):
    model = Proprietaires
    fields = ['raison_sociale', 'nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'persons/proprietaires_list.html'
    context_object_name = 'proprietaires'


class Proprietaires_CreateView(CreateView):
    model = Proprietaires
    form_class = ProprietaireForm
    template_name = 'persons/proprietaire_create.html'
    success_url = reverse_lazy('persons:proprietaires_list')
    context_object_name = 'proprietaire'


class Proprietaires_UpdateView(UpdateView):
    model = Proprietaires
    form_class = ProprietaireForm
    template_name = 'persons/proprietaire_update.html'
    success_url = reverse_lazy('persons:proprietaires_list')

def Proprietaire_DeleteView(request, pk):
    proprio = get_object_or_404(Proprietaires, id=pk)
    nom = proprio.nom_complet
    proprio.delete()
    messages.success(request, f'Le proprietaire {nom} a été supprimé avec succès.')
    return redirect('persons:proprietaires_list')


# ============================================================
# VUES POUR LES LOCATAIRES
# ============================================================

class Locataires_ListView(ListView):
    # model = Locataires
    fields = ['nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'persons/locataires_list.html'
    context_object_name = 'locataires'

    def get_queryset(self):

        qs = Locataires.objects.all()


        search = self.request.GET.get('search')
        actif = self.request.GET.get('actif')

        if search:
            qs = qs.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search)
            )

        if actif == '1':
            qs = qs.filter(actif=True)
        elif actif == '0':
            qs = qs.filter(actif=False)


        return qs


class Locataires_CreateView(CreateView):
    model = Locataires
    form_class = LocataireForm
    template_name = 'persons/locataire_create.html'
    success_url = reverse_lazy('persons:locataires_list')
    context_object_name = 'locataires'


class Locataires_UpdateView(UpdateView):
    model = Locataires
    form_class = LocataireForm
    template_name = 'persons/locataire_update.html'
    success_url = reverse_lazy('persons:locataires_list')

def Locataire_DeleteView(request, pk):
    locataire = get_object_or_404(Locataires, id=pk)
    nom = locataire.nom_complet
    locataire.delete()
    messages.success(request, f'Le locataire {nom} a été supprimé avec succès.')
    return redirect('persons:locataires_list')


class Locataires_DetailView(DetailView):
    """Vue détaillée d'un locataire avec tous ses contrats et historique"""
    model = Locataires
    template_name = 'persons/locataire_detail.html'
    context_object_name = 'locataire'

    def get_queryset(self):
        # ✅ Optimiser les requêtes
        return Locataires.objects.prefetch_related('contrats')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = self.get_object()
        today = timezone.now().date()

        # ============================================================
        # RÉCUPÉRER TOUS LES CONTRATS DU LOCATAIRE
        # ============================================================
        # ✅ Via la table intermédiaire ContratLocataire
        relations_contrats = ContratLocataire.objects.filter(
            locataire=locataire
        ).select_related(
            'contrat__appartement__immeuble'
        ).prefetch_related(
            'contrat__locataires'
        ).order_by('-contrat__date_debut')

        # Séparer les contrats actifs et anciens
        contrats_actifs_relations = relations_contrats.filter(
            date_sortie__isnull=True,  # Locataire toujours présent
            contrat__actif=True
        )

        contrats_anciens_relations = relations_contrats.filter(
            Q(date_sortie__isnull=False) |  # Locataire sorti
            Q(contrat__actif=False)  # Contrat inactif
        )

        # ✅ CORRECTION : Extraire les objets Contrats pour le template
        contrats = Contrats.objects.filter(
            id__in=relations_contrats.values_list('contrat_id', flat=True)
        ).select_related(
            'appartement__immeuble'
        ).prefetch_related(
            'locataires'
        ).order_by('-date_debut')

        # ============================================================
        # DÉTERMINER LE CONTRAT ACTUEL PRINCIPAL
        # ============================================================
        contrat_actuel = None
        relation_principale = contrats_actifs_relations.filter(
            principal=True,
            contrat__date_debut__lte=today
        ).filter(
            Q(contrat__date_fin__isnull=True) | Q(contrat__date_fin__gte=today)
        ).first()

        if relation_principale:
            contrat_actuel = relation_principale.contrat
        elif contrats_actifs_relations.exists():
            # Fallback : premier contrat actif par ordre
            contrat_actuel = contrats_actifs_relations.first().contrat

        # ============================================================
        # RÉCUPÉRER LES PAIEMENTS
        # ============================================================
        paiements_recents = PaiementLocataire.objects.none()
        nb_paiements_total = 0

        if contrat_actuel:
            # Paiements des 12 derniers mois pour tous les contrats actifs du locataire
            contrats_actifs_ids = list(contrats_actifs_relations.values_list('contrat_id', flat=True))

            paiements_recents = PaiementLocataire.objects.filter(
                contrat_id__in=contrats_actifs_ids
            ).select_related(
                'contrat__appartement__immeuble'
            ).order_by('-mois', '-date_paiement')[:12]

            nb_paiements_total = PaiementLocataire.objects.filter(
                contrat_id__in=contrats_actifs_ids
            ).count()

        # ============================================================
        # RÉCUPÉRER LES QUITTANCES
        # ============================================================
        quittances_recentes = Quittance.objects.none()
        nb_quittances = 0

        if contrat_actuel:
            contrats_actifs_ids = list(contrats_actifs_relations.values_list('contrat_id', flat=True))

            quittances_recentes = Quittance.objects.filter(
                contrat_id__in=contrats_actifs_ids
            ).select_related(
                'contrat__appartement__immeuble'
            ).prefetch_related(
                'contrat__locataires'
            ).order_by('-mois', '-date_generation')[:12]

            nb_quittances = Quittance.objects.filter(
                contrat_id__in=contrats_actifs_ids
            ).count()

        # ============================================================
        # STATISTIQUES
        # ============================================================
        stats = {
            'nb_contrats_actifs': contrats_actifs_relations.count(),
            'nb_contrats_total': relations_contrats.count(),
            'nb_paiements': nb_paiements_total,
            'nb_quittances': nb_quittances,
        }

        # Si contrat actuel, ajouter des stats supplémentaires
        if contrat_actuel:
            stats.update({
                'loyer_mensuel': contrat_actuel.loyer_total,
                'appartement': contrat_actuel.appartement,
                'immeuble': contrat_actuel.appartement.immeuble,
            })

        # ============================================================
        # CONTEXTE
        # ============================================================
        context.update({
            # ✅ CORRECTION : Passer les objets Contrats, pas les relations
            'contrats': contrats,  # Pour l'onglet "Contrats"
            'contrat_actuel': contrat_actuel,  # Pour l'onglet "Informations" et "Documents"
            'relation_principale': relation_principale,

            # Paiements et quittances
            'paiements_recents': paiements_recents,
            'quittances_recentes': quittances_recentes,

            # Statistiques
            'stats': stats,
            'nb_quittances': nb_quittances,
        })

        return context