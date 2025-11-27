from django.shortcuts import render, redirect

from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from datetime import date
from .models import PaiementLocataire
from .forms import PaiementLocataireForm
from contrats.models import Contrats

class PaiementsContrats_list(ListView):
    model = Contrats
    fields = ['raison_sociale', 'nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'paiements/contrats_paiements_list.html'
    context_object_name = 'contrats'


def paiements_accueil(request):
    return render(request, "paiements/paiements_accueil.html")


class PaiementCreateView(LoginRequiredMixin, CreateView):
    model = PaiementLocataire
    form_class = PaiementLocataireForm
    template_name = 'paiements/paiement_form.html'
    # success_url = reverse_lazy('paiements:paiements_contrats_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['contrat_id'] = self.kwargs.get('contrat_id')
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        paiement = form.save(commit=False)
        paiement.created_by = self.request.user
        paiement.save()

        # Afficher les warnings s'il y en a
        for warning in form.get_warnings():
            messages.warning(self.request, warning)

        messages.success(
            self.request,
            f'Paiement de {paiement.total}€ enregistré avec succès'
        )

        return super().form_valid(form)

    def get_success_url(self):
        # self.object contient l'instance créée/modifiée
        return reverse('paiements:paiements_locataires_list', kwargs={'contrat_id': self.object.contrat.id})
    
class PaiementUpdateView(LoginRequiredMixin, UpdateView):
    model = PaiementLocataire
    form_class = PaiementLocataireForm
    template_name = 'paiements/paiement_update_form.html'
    # success_url = reverse_lazy('paiements:paiements_contrats_list')

    def get_success_url(self):
        # self.object contient l'instance créée/modifiée
        return reverse('paiements:paiements_locataires_list', kwargs={'contrat_id': self.object.contrat.id})



class PaiementsLocataire_List(ListView):
    # model = PaiementLocataire
    fields = ['mois', 'date_echeance', 'date_paiement','loyer', 'charges', 'statut', 'valide']
    template_name = 'paiements/locataires_paiements_list.html'
    context_object_name = 'paiements'

    
    def get_context_data(self, **kwargs):
        """Ajouter des données au template"""
        context = super().get_context_data(**kwargs)

        # Ajouter le contrat au contexte pour l'afficher
        contrat_id = self.kwargs.get('contrat_id')
        if True:
            context['contrat'] = get_object_or_404(Contrats, pk=contrat_id)
            context['locataire'] = Contrats.objects.get(id=contrat_id).locataire.nom_complet
        return context    

    def get_queryset(self):
        contrat_id = self.kwargs.get('contrat_id')
        return (PaiementLocataire.objects.filter(contrat_id=contrat_id))


def paiement_delete_item(request, pk):
    P =PaiementLocataire.objects.get(id=pk)
    contrat_id = P.contrat.id
    PaiementLocataire.objects.get(id=pk).delete()
    return redirect('paiements:paiements_locataires_list', contrat_id=contrat_id)

