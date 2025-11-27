from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from persons.models import Proprietaires, Locataires
from persons.forms import ProprietaireForm, LocataireForm
from django.views.generic import DetailView
from django.db.models import Q
from django.utils import timezone
from .models import Locataires
from contrats.models import Contrats
from paiements.models import PaiementLocataire
from quittances.models import Quittance


class Locataires_DetailView(DetailView):
    model = Locataires
    template_name = 'persons/locataire_detail.html'
    context_object_name = 'locataire'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = self.get_object()

        # Récupérer tous les contrats du locataire
        contrats = Contrats.objects.filter(
            locataire=locataire
        ).select_related(
            'appartement',
            'appartement__immeuble'
        ).order_by('-date_debut')

        # Déterminer le contrat actuel
        today = timezone.now().date()
        contrat_actuel = contrats.filter(
            actif=True,
            date_debut__lte=today
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=today)
        ).first()

        # Récupérer les paiements récents (derniers 12 mois ou tous si moins)
        paiements_recents = PaiementLocataire.objects.none()
        if contrat_actuel:
            paiements_recents = PaiementLocataire.objects.filter(
                contrat__locataire=locataire
            ).select_related(
                'contrat',
                'contrat__appartement',
                'contrat__appartement__immeuble'
            ).order_by('-mois', '-date_paiement')[:12]

        # Récupérer les quittances du locataire
        quittances_recentes = Quittance.objects.none()
        nb_quittances = 0
        if contrat_actuel:
            # Toutes les quittances du locataire (tous ses contrats)
            quittances_recentes = Quittance.objects.filter(
                contrat__locataire=locataire
            ).select_related(
                'contrat',
                'contrat__appartement',
                'contrat__appartement__immeuble'
            ).order_by('-mois', '-date_generation')[:12]

            # Nombre total de quittances
            nb_quittances = Quittance.objects.filter(
                contrat__locataire=locataire
            ).count()

        context.update({
            'contrats': contrats,
            'contrat_actuel': contrat_actuel,
            'paiements_recents': paiements_recents,
            'quittances_recentes': quittances_recentes,
            'nb_quittances': nb_quittances,
        })

        return context


def persons_accueil(request):
    return render(request, "persons/persons_accueil.html")


class Proprietaires_ListView(ListView):
    model=Proprietaires
    fields = ['raison_sociale', 'nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'persons/proprietaires_list.html'
    context_object_name = 'proprietaires'


class Proprietaires_CreateView(CreateView):
    model=Proprietaires
    form_class = ProprietaireForm
    template_name = 'persons/proprietaire_create.html'
    success_url = reverse_lazy('persons:proprietaires_list')
    context_object_name = 'proprietaire'


class Proprietaires_UpdateView(UpdateView):
    model=Proprietaires
    form_class = ProprietaireForm
    template_name = 'persons/proprietaire_update.html'
    success_url = reverse_lazy('persons:proprietaires_list')


class Locataires_ListView(ListView):
    model=Locataires
    fields = ['nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'persons/locataires_list.html'
    context_object_name = 'locat'


class Locataires_CreateView(CreateView):
    model=Locataires
    form_class = LocataireForm
    template_name = 'persons/locataire_create.html'
    success_url = reverse_lazy('persons:locataires_list')
    context_object_name = 'locataires'


class Locataires_UpdateView(UpdateView):
    model = Locataires
    form_class = LocataireForm
    template_name = 'persons/locataire_update.html'
    success_url = reverse_lazy('persons:locataires_list')


class Locataires_DetailView_old(DetailView):
    model = Locataires
    template_name = 'persons/locataire_detail.html'
    context_object_name = 'locataire'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = self.get_object()

        # Récupérer tous les contrats du locataire
        contrats = Contrats.objects.filter(
            locataire=locataire
        ).select_related(
            'appartement',
            'appartement__immeuble'
        ).order_by('-date_debut')

        # Déterminer le contrat actuel
        today = timezone.now().date()
        contrat_actuel = contrats.filter(
            actif=True,
            date_debut__lte=today
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=today)
        ).first()

        # Récupérer les paiements récents (derniers 12 mois ou tous si moins)
        paiements_recents = PaiementLocataire.objects.none()
        if contrat_actuel:
            paiements_recents = PaiementLocataire.objects.filter(
                contrat__locataire=locataire
            ).select_related(
                'contrat',
                'contrat__appartement',
                'contrat__appartement__immeuble'
            ).order_by('-mois', '-date_paiement')[:12]

        context.update({
            'contrats': contrats,
            'contrat_actuel': contrat_actuel,
            'paiements_recents': paiements_recents,
        })

        return context


class Locataires_DetailView(DetailView):
    model = Locataires
    template_name = 'persons/locataire_detail.html'
    context_object_name = 'locataire'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locataire = self.get_object()

        # Récupérer tous les contrats du locataire
        contrats = Contrats.objects.filter(
            locataire=locataire
        ).select_related(
            'appartement',
            'appartement__immeuble'
        ).order_by('-date_debut')

        # Déterminer le contrat actuel
        today = timezone.now().date()
        contrat_actuel = contrats.filter(
            actif=True,
            date_debut__lte=today
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=today)
        ).first()

        # Récupérer les paiements récents (derniers 12 mois ou tous si moins)
        paiements_recents = PaiementLocataire.objects.none()
        if contrat_actuel:
            paiements_recents = PaiementLocataire.objects.filter(
                contrat__locataire=locataire
            ).select_related(
                'contrat',
                'contrat__appartement',
                'contrat__appartement__immeuble'
            ).order_by('-mois', '-date_paiement')[:12]

        # Récupérer les quittances du locataire
        quittances_recentes = Quittance.objects.none()
        nb_quittances = 0
        if contrat_actuel:
            # Toutes les quittances du locataire (tous ses contrats)
            quittances_recentes = Quittance.objects.filter(
                contrat__locataire=locataire
            ).select_related(
                'contrat',
                'contrat__appartement',
                'contrat__appartement__immeuble'
            ).order_by('-mois', '-date_generation')[:12]

            # Nombre total de quittances
            nb_quittances = Quittance.objects.filter(
                contrat__locataire=locataire
            ).count()

        context.update({
            'contrats': contrats,
            'contrat_actuel': contrat_actuel,
            'paiements_recents': paiements_recents,
            'quittances_recentes': quittances_recentes,
            'nb_quittances': nb_quittances,
        })

        return context