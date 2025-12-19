from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from datetime import date
from django.db.models import Sum, Q, Count
from django.db.models.functions import ExtractYear

from .models import PaiementLocataire
from .forms import PaiementLocataireForm
from contrats.models import Contrats


def paiements_accueil(request):
    return render(request, "paiements/paiements_accueil.html")


# ============================================================
# VUE PRINCIPALE : LISTE DE TOUS LES PAIEMENTS
# ============================================================

class PaiementListView(LoginRequiredMixin, ListView):
    """Liste globale de tous les paiements avec filtres et statistiques"""
    model = PaiementLocataire
    template_name = 'paiements/paiement_list.html'
    context_object_name = 'paiements'
    paginate_by = 50

    def get_queryset(self):
        queryset = PaiementLocataire.objects.select_related(
            'contrat__appartement__immeuble',
            'contrat__appartement'
        ).prefetch_related(
            'contrat__locataires'
        ).order_by('-mois', '-date_echeance')

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(contrat__locataires__nom__icontains=search) |
                Q(contrat__locataires__prenom__icontains=search)
            ).distinct()

        mois = self.request.GET.get('mois')
        if mois:
            queryset = queryset.filter(mois__startswith=mois)

        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        valide = self.request.GET.get('valide')
        if valide:
            queryset = queryset.filter(valide=(valide == '1'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculer les statistiques
        queryset = self.get_queryset()

        stats = {
            'payes_count': queryset.filter(statut='recu').count(),
            'payes_montant': queryset.filter(statut='recu').aggregate(
                total=Sum('loyer') + Sum('charges') + Sum('autres')
            )['total'] or 0,

            'attente_count': queryset.filter(statut='attente').count(),
            'attente_montant': queryset.filter(statut='attente').aggregate(
                total=Sum('loyer') + Sum('charges') + Sum('autres')
            )['total'] or 0,

            'retard_count': queryset.filter(statut='retard').count(),
            'retard_montant': queryset.filter(statut='retard').aggregate(
                total=Sum('loyer') + Sum('charges') + Sum('autres')
            )['total'] or 0,
        }

        stats['total_count'] = queryset.count()
        stats['total_montant'] = stats['payes_montant'] + stats['attente_montant'] + stats['retard_montant']

        context['stats'] = stats

        return context


# ============================================================
# VUE : LISTE DES CONTRATS AVEC PAIEMENTS
# ============================================================

class PaiementsContrats_list(ListView):
    model = Contrats
    template_name = 'paiements/contrats_paiements_list.html'
    context_object_name = 'contrats'

    def get_queryset(self):
        return Contrats.objects.select_related(
            'appartement__immeuble'
        ).prefetch_related(
            'locataires'
        ).filter(actif=True).order_by('-date_debut')


# ============================================================
# VUE : LISTE DES PAIEMENTS D'UN LOCATAIRE/CONTRAT
# ============================================================

class PaiementsLocataire_List(ListView):
    fields = ['mois', 'date_echeance', 'date_paiement', 'loyer', 'charges', 'statut', 'valide']
    template_name = 'paiements/locataires_paiements_list.html'
    context_object_name = 'paiements'

    def get_context_data(self, **kwargs):
        """Ajouter des données au template"""
        context = super().get_context_data(**kwargs)

        # Ajouter le contrat au contexte pour l'afficher
        contrat_id = self.kwargs.get('contrat_id')
        queryset = self.get_queryset()

        totaux = queryset.annotate(
            annee=ExtractYear('mois')
        ).values('annee').annotate(
            total_loyer=Sum('loyer'),
            total_charges=Sum('charges')
        ).order_by('annee')

        contrat = get_object_or_404(
            Contrats.objects.prefetch_related('locataires'),
            pk=contrat_id
        )

        context['contrat'] = contrat
        context['locataires_display'] = contrat.get_locataires_display()
        context['locataire_principal'] = contrat.get_locataire_principal()
        context['totaux'] = totaux

        return context

    def get_queryset(self):
        contrat_id = self.kwargs.get('contrat_id')
        queryset = PaiementLocataire.objects.filter(
            contrat_id=contrat_id
        ).select_related('contrat__appartement__immeuble')
        return queryset


# ============================================================
# CRÉATION ET MODIFICATION DE PAIEMENTS
# ============================================================

class PaiementCreateView(LoginRequiredMixin, CreateView):
    model = PaiementLocataire
    form_class = PaiementLocataireForm
    template_name = 'paiements/paiement_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['contrat_id'] = self.kwargs.get('contrat_id')
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        paiement = form.save(commit=False)
        paiement.created_by = self.request.user
        paiement.save()

        try:
            from quittances.utils import QuittanceManager

            # Afficher les warnings s'il y en a
            if hasattr(form, 'get_warnings'):
                for warning in form.get_warnings():
                    messages.warning(self.request, warning)

            messages.success(
                self.request,
                f'Paiement de {paiement.loyer + paiement.charges + (paiement.autres or 0)}€ enregistré avec succès'
            )

            quittance = QuittanceManager.generer_depuis_paiement(paiement)
            if quittance:
                messages.success(
                    self.request,
                    f'Quittance n° {quittance.numero} enregistrée avec succès'
                )
        except ImportError:
            # Module quittances pas encore disponible
            messages.success(
                self.request,
                f'Paiement enregistré avec succès'
            )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('paiements:paiements_locataires_list', kwargs={'contrat_id': self.object.contrat.id})


class PaiementUpdateView(LoginRequiredMixin, UpdateView):
    model = PaiementLocataire
    form_class = PaiementLocataireForm
    template_name = 'paiements/paiement_update_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['contrat_id'] = self.object.contrat.id
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Paiement mis à jour avec succès.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('paiements:paiements_locataires_list', kwargs={'contrat_id': self.object.contrat.id})


# ============================================================
# ACTIONS SUR LES PAIEMENTS
# ============================================================

def paiement_delete_item(request, pk):
    paiement = get_object_or_404(PaiementLocataire, id=pk)
    contrat_id = paiement.contrat.id
    paiement.delete()
    messages.success(request, 'Paiement supprimé avec succès.')
    return redirect('paiements:paiements_locataires_list', contrat_id=contrat_id)


# @LoginRequiredMixin
def paiement_valider(request, pk):
    """Valide un paiement"""
    paiement = get_object_or_404(PaiementLocataire, id=pk)

    if request.method == 'POST':
        paiement.valide = True
        paiement.save()
        messages.success(request, f'Paiement du {paiement.mois.strftime("%m/%Y")} validé avec succès.')
        return redirect('paiements:paiement_list')

    return redirect('paiements:paiement_list')