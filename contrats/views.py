# contrats/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import date

from .models import Contrats, ContratLocataire
from .forms import (
    ContratForm, AjouterLocataireContratForm,
    CreerNouveauLocataireForm
)
from persons.models import Locataires


# ============================================================
# VUES DE BASE POUR LES CONTRATS
# ============================================================

@method_decorator(login_required, name='dispatch')
class Contrats_ListView(ListView):
    model = Contrats
    template_name = 'contrats/contrats_list.html'
    context_object_name = 'contrats'

    def get_queryset(self):
        return Contrats.objects.select_related('appartement').prefetch_related('locataires')


@method_decorator(login_required, name='dispatch')
class Contrats_CreateView(CreateView):
    model = Contrats
    form_class = ContratForm
    template_name = 'contrats/contrat_create.html'
    success_url = reverse_lazy('contrats:contrats_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Contrat créé avec succès. Vous pouvez maintenant ajouter les locataires.'
        )
        # Rediriger vers la gestion des locataires
        return redirect('contrats:contrat_locataires', contrat_id=self.object.id)


@method_decorator(login_required, name='dispatch')
class Contrats_UpdateView(UpdateView):
    model = Contrats
    form_class = ContratForm
    template_name = 'contrats/contrat_update.html'
    success_url = reverse_lazy('contrats:contrats_list')

    def form_valid(self, form):
        messages.success(self.request, 'Contrat mis à jour avec succès.')
        return super().form_valid(form)


@login_required
def contrat_delete_item(request, pk):
    contrat = get_object_or_404(Contrats, id=pk)
    appartement = contrat.appartement
    contrat.delete()
    messages.success(request, f'Contrat pour {appartement} supprimé avec succès.')
    return redirect('contrats:contrats_list')


def contrats_accueil(request):
    return redirect('home')


# ============================================================
# GESTION DES LOCATAIRES D'UN CONTRAT
# ============================================================

@login_required
def contrat_locataires_list(request, contrat_id):
    """Affiche la liste des locataires d'un contrat"""
    contrat = get_object_or_404(Contrats, pk=contrat_id)

    # Récupérer tous les locataires (actifs et sortis)
    relations_locataires = ContratLocataire.objects.filter(
        contrat=contrat
    ).select_related('locataire').order_by('ordre', 'date_entree')

    # Séparer actifs et sortis
    locataires_actifs = relations_locataires.filter(date_sortie__isnull=True)
    locataires_sortis = relations_locataires.filter(date_sortie__isnull=False)

    context = {
        'contrat': contrat,
        'locataires_actifs': locataires_actifs,
        'locataires_sortis': locataires_sortis,
        'nb_actifs': locataires_actifs.count(),
    }

    return render(request, 'contrats/contrat_locataire_list.html', context)


@login_required
def ajouter_locataire_contrat(request, contrat_id):
    """Ajoute un locataire existant à un contrat"""
    contrat = get_object_or_404(Contrats, pk=contrat_id)

    if request.method == 'POST':
        form = AjouterLocataireContratForm(request.POST, contrat=contrat)

        if form.is_valid():
            locataire = form.cleaned_data['locataire']
            principal = form.cleaned_data['principal']
            role = form.cleaned_data['role']

            # Ajouter le locataire
            contrat.ajouter_locataire(
                locataire=locataire,
                principal=principal,
                role=role
            )

            messages.success(
                request,
                f'{locataire.nom_complet} a été ajouté au contrat.'
            )
            return redirect('contrats:contrat_locataires', contrat_id=contrat.id)
    else:
        form = AjouterLocataireContratForm(contrat=contrat)

    context = {
        'form': form,
        'contrat': contrat,
    }

    return render(request, 'contrats/ajouter_locataire.html', context)


@login_required
def creer_et_ajouter_locataire(request, contrat_id):
    """Crée un nouveau locataire et l'ajoute au contrat"""
    contrat = get_object_or_404(Contrats, pk=contrat_id)

    if request.method == 'POST':
        form = CreerNouveauLocataireForm(request.POST)

        if form.is_valid():
            # Créer le locataire
            locataire = form.save(commit=False)
            locataire.actif = True
            locataire.save()

            # L'ajouter au contrat
            principal = form.cleaned_data.get('principal', False)
            role = form.cleaned_data.get('role', 'cotitulaire')

            contrat.ajouter_locataire(
                locataire=locataire,
                principal=principal,
                role=role
            )

            messages.success(
                request,
                f'Locataire {locataire.nom_complet} créé et ajouté au contrat.'
            )
            return redirect('contrats:contrat_locataires', contrat_id=contrat.id)
    else:
        form = CreerNouveauLocataireForm()

    context = {
        'form': form,
        'contrat': contrat,
    }

    return render(request, 'contrats/creer_nouveau_locataire.html', context)


@login_required
def retirer_locataire_contrat(request, contrat_id, relation_id):
    """Retire un locataire d'un contrat (marque comme sorti)"""
    contrat = get_object_or_404(Contrats, pk=contrat_id)
    relation = get_object_or_404(ContratLocataire, pk=relation_id, contrat=contrat)

    if request.method == 'POST':
        date_sortie_str = request.POST.get('date_sortie')

        if date_sortie_str:
            try:
                relation.date_sortie = date.fromisoformat(date_sortie_str)
            except ValueError:
                relation.date_sortie = date.today()
        else:
            relation.date_sortie = date.today()

        relation.save()

        messages.success(
            request,
            f'{relation.locataire.nom_complet} a été retiré du contrat.'
        )
        return redirect('contrats:contrat_locataires', contrat_id=contrat.id)

    context = {
        'contrat': contrat,
        'relation': relation,
    }

    return render(request, 'contrats/retirer_locataire.html', context)


@login_required
def definir_principal(request, contrat_id, relation_id):
    """Définit un locataire comme contact principal"""
    contrat = get_object_or_404(Contrats, pk=contrat_id)
    relation = get_object_or_404(ContratLocataire, pk=relation_id, contrat=contrat)

    # Retirer le flag principal de tous les autres
    ContratLocataire.objects.filter(
        contrat=contrat,
        principal=True
    ).update(principal=False)

    # Définir le nouveau principal
    relation.principal = True
    relation.save()

    messages.success(
        request,
        f'{relation.locataire.nom_complet} est maintenant le contact principal.'
    )

    return redirect('contrats:contrat_locataires', contrat_id=contrat.id)


@login_required
def modifier_ordre_locataires(request, contrat_id):
    """Modifie l'ordre d'affichage des locataires"""
    contrat = get_object_or_404(Contrats, pk=contrat_id)

    if request.method == 'POST':
        # Récupérer les IDs dans le nouvel ordre
        ordre_ids = request.POST.getlist('ordre[]')

        for index, relation_id in enumerate(ordre_ids, start=1):
            ContratLocataire.objects.filter(
                id=relation_id,
                contrat=contrat
            ).update(ordre=index)

        messages.success(request, 'Ordre des locataires mis à jour.')
        return redirect('contrats:contrat_locataires', contrat_id=contrat.id)

    relations = ContratLocataire.objects.filter(
        contrat=contrat,
        date_sortie__isnull=True
    ).order_by('ordre')

    context = {
        'contrat': contrat,
        'relations': relations,
    }

    return render(request, 'contrats/modifier_ordre_locataires.html', context)