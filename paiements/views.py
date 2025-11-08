from django.shortcuts import render

from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
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





class PaiementCreateView_old(LoginRequiredMixin, CreateView):
    model = PaiementLocataire
    form_class = PaiementLocataireForm
    template_name = 'paiements/paiement_form.html'

    def get_success_url(self):
        # Redirection dynamique vers le détail du paiement créé
        return reverse_lazy('paiements:detail', kwargs={'pk': self.object.pk})

    def get_initial(self):
        """Pré-remplir le formulaire"""
        initial = super().get_initial()

        # Récupérer le contrat depuis l'URL
        contrat_id = self.kwargs.get('contrat_id')
        if contrat_id:
            contrat = get_object_or_404(Contrats, pk=contrat_id)
            initial.update({
                'contrat': contrat,
                'loyer': contrat.loyer_mensuel,
                'charges': contrat.charges_mensuelles,
                'date_paiement': date.today(),
                'mode_paiement': 'virement',
            })

        return initial

    def get_form_kwargs(self):
        """Passer des arguments au formulaire"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Traitement avant sauvegarde"""
        paiement = form.save(commit=False)

        # Ajouter l'utilisateur qui crée le paiement
        paiement.created_by = self.request.user

        # Auto-calcul des valeurs si non fournies
        if not paiement.loyer:
            paiement.loyer = paiement.contrat.loyer_mensuel
        if not paiement.charges:
            paiement.charges = paiement.contrat.charges_mensuelles

        # Définir l'échéance automatiquement
        if not paiement.date_echeance:
            paiement.date_echeance = paiement.mois.replace(day=5)

        # Sauvegarder
        paiement.save()

        # Message de succès
        messages.success(
            self.request,
            f'Paiement de {paiement.total}€ enregistré pour '
            f'{paiement.contrat.locataire.nom_complet}'
        )

        # # Générer automatiquement une quittance si paiement complet
        # if paiement.est_complet:
        #     from quittances.utils import QuittanceManager
        #     try:
        #         quittance = QuittanceManager.generer_quittance(
        #             paiement.contrat,
        #             paiement.mois
        #         )
        #         messages.info(
        #             self.request,
        #             f'Quittance {quittance.numero} générée automatiquement'
        #         )
        #     except Exception as e:
        #         messages.warning(
        #             self.request,
        #             f'Erreur lors de la génération de la quittance: {e}'
        #         )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Si le formulaire est invalide"""
        messages.error(
            self.request,
            'Erreur dans le formulaire. Veuillez vérifier les informations.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Ajouter des données au template"""
        context = super().get_context_data(**kwargs)

        # Ajouter le contrat au contexte pour l'afficher
        contrat_id = self.kwargs.get('contrat_id')
        if contrat_id:
            context['contrat'] = get_object_or_404(Contrats, pk=contrat_id)

        # Ajouter les derniers paiements
        if 'contrat' in context:
            context['derniers_paiements'] = PaiementLocataire.objects.filter(
                contrat=context['contrat']
            ).order_by('-mois')[:5]

        return context


def paiements_accueil(request):
    return render(request, "paiements/paiements_accueil.html")


class PaiementCreateView(LoginRequiredMixin, CreateView):
    model = PaiementLocataire
    form_class = PaiementLocataireForm
    template_name = 'paiements/paiement_form.html'
    success_url = reverse_lazy('paiements:paiements_contrats_list')

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
    
class PaiementUpdateView(LoginRequiredMixin, UpdateView):
    model = PaiementLocataire
    form_class = PaiementLocataireForm
    template_name = 'paiements/paiement_form.html'
    success_url = reverse_lazy('paiements:paiements_contrats_list')

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

class PaiementsLocataire_List(ListView):
    # model = PaiementLocataire
    fields = ['mois', 'date_echeance', 'date_paiement','loyer', 'charges', 'statut', 'valide']
    template_name = 'paiements/locataires_paiements_list.html'
    context_object_name = 'paiements'

    def get_queryset(self):
        contrat_id = self.kwargs.get('contrat_id')
        return PaiementLocataire.objects.filter(contrat_id=contrat_id)
    
    def get_context_data(self, **kwargs):
        """Ajouter des données au template"""
        context = super().get_context_data(**kwargs)

        # Ajouter le contrat au contexte pour l'afficher
        contrat_id = self.kwargs.get('contrat_id')
        if True:
            context['contrat'] = get_object_or_404(Contrats, pk=contrat_id)
            context['locataire'] = Contrats.objects.get(id=contrat_id).locataire.nom_complet
        return context    



