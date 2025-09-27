# apps/immeubles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .models import Immeuble, Appartement #, TypeAppartement
from .forms import ImmeubleForm, AppartementForm, ImmeubleSearchForm


#@method_decorator(login_required, name='dispatch')
class ImmeubleListView(ListView):
    """Liste des immeubles"""
    model = Immeuble
    template_name = 'immeubles/immeuble_list.html'
    context_object_name = 'immeubles'
    paginate_by = 12

    def get_queryset(self):
        '''
        queryset = Immeuble.objects.filter(actif=True).annotate(
            nb_appartements=Count('appartements'),
            nb_appartements_loues=Count('appartements', filter=Q(appartements__loue=True))
        )
        '''
        queryset = Immeuble.objects.all()
        # Filtres de recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(ville__icontains=search) |
                Q(adresse__icontains=search)
            )

        return queryset.order_by('nom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ImmeubleSearchForm(self.request.GET)
        return context


#@method_decorator(login_required, name='dispatch')
class ImmeubleDetailView(DetailView):
    """Détail d'un immeuble"""
    model = Immeuble
    template_name = 'immeubles/immeuble_detail.html'
    context_object_name = 'immeuble'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        immeuble = self.object



        # Appartements avec leurs statistiques
        appartements = immeuble.appartements.select_related(
            'type_appartement'
        ).prefetch_related(
            'contrats__locataire'
        ).order_by('etage', 'numero')
        """
        context['appartements'] = appartements

        # Statistiques de l'immeuble
        context['stats'] = {
            'nb_appartements': appartements.count(),
            'nb_loues': appartements.filter(loue=True).count(),
            'surface_totale': sum(apt.surface for apt in appartements),
            'revenus_mensuels': sum(
                apt.contrat_actuel.loyer_total
                for apt in appartements
                if apt.contrat_actuel
            )
        }

        # Contrats actifs
        context['contrats_actifs'] = [
            apt.contrat_actuel for apt in appartements
            if apt.contrat_actuel
        ]
        """
        return context


#@method_decorator(gestionnaire_required, name='dispatch')
class ImmeubleCreateView(CreateView):
    """Création d'un immeuble"""
    model = Immeuble
    form_class = ImmeubleForm
    template_name = 'immeubles/immeuble_form.html'
    success_url = reverse_lazy('immeubles:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Immeuble "{form.instance.nom}" créé avec succès.')
        return super().form_valid(form)


#@method_decorator(gestionnaire_required, name='dispatch')
class ImmeubleUpdateView(UpdateView):
    """Modification d'un immeuble"""
    model = Immeuble
    form_class = ImmeubleForm
    template_name = 'immeuble/immeuble_form.html'

    def get_success_url(self):
        return reverse_lazy('immeuble:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f'Immeuble "{form.instance.nom}" modifié avec succès.')
        return super().form_valid(form)


# Vues pour les appartements
@method_decorator(login_required, name='dispatch')
class AppartementListView(ListView):
    """Liste des appartements"""
    model = Appartement
    template_name = 'immeuble/appartement_list.html'
    context_object_name = 'appartements'
    paginate_by = 20

    def get_queryset(self):
        queryset = Appartement.objects.select_related(
            'immeuble', 'type_appartement'
        ).prefetch_related(
            'contrats__locataire'
        )

        # Filtres
        immeuble_id = self.request.GET.get('immeuble')
        if immeuble_id:
            queryset = queryset.filter(immeuble_id=immeuble_id)

        statut = self.request.GET.get('statut')
        if statut == 'libre':
            queryset = queryset.filter(loue=False)
        elif statut == 'loue':
            queryset = queryset.filter(loue=True)

        return queryset.order_by('immeuble__nom', 'etage', 'numero')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['immeubles'] = Immeuble.objects.filter(actif=True)
        context['current_filters'] = {
            'immeuble': self.request.GET.get('immeuble', ''),
            'statut': self.request.GET.get('statut', ''),
        }
        return context


from django.shortcuts import render

# Create your views here.
