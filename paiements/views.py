from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.db.models import Sum, Q, Count
from django.db.models.functions import ExtractYear
from django.http import JsonResponse

from .models import PaiementLocataire
from .forms import PaiementLocataireForm
from contrats.models import Contrats
from decimal import Decimal
from datetime import date

from .models import (
    TypeDepense,
    DepenseProprietaire,
    RepartitionDepense
)

from .forms import (
    TypeDepenseForm,
    DepenseProprietaireForm,
    RepartitionDepenseForm,
    RepartitionAutomatiqueForm,
    FiltreDepensesForm
)
from immeuble.models import Appartement

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

        stats = {'payes_count': queryset.filter(statut='recu').count(),
                 'payes_montant': queryset.filter(statut='recu').aggregate(
                     total=Sum('loyer') + Sum('charges') + Sum('autres')
                 )['total'] or 0, 'attente_count': queryset.filter(statut='attente').count(),
                 'attente_montant': queryset.filter(statut='attente').aggregate(
                     total=Sum('loyer') + Sum('charges') + Sum('autres')
                 )['total'] or 0, 'retard_count': queryset.filter(statut='retard').count(),
                 'retard_montant': queryset.filter(statut='retard').aggregate(
                     total=Sum('loyer') + Sum('charges') + Sum('autres')
                 )['total'] or 0, 'total_count': queryset.count()}

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


# =============================================================================
# VUES POUR LES TYPES DE DÉPENSES
# =============================================================================

@login_required
def type_depense_liste(request):
    """Liste des types de dépenses"""
    types = TypeDepense.objects.all()

    # Statistiques
    stats = {
        'total': types.count(),
        'actifs': types.filter(actif=True).count(),
        'recurrents': types.filter(recurrent=True).count(),
    }

    context = {
        'types_depenses': types,
        'stats': stats,
    }
    return render(request, 'paiements/type_depense_liste.html', context)


@login_required
def type_depense_create(request):
    """Créer un type de dépense"""
    if request.method == 'POST':
        form = TypeDepenseForm(request.POST)
        if form.is_valid():
            type_depense = form.save()
            messages.success(request, f'Type de dépense "{type_depense.nom}" créé avec succès.')
            return redirect('paiements:type_depense_liste')
    else:
        form = TypeDepenseForm()

    return render(request, 'paiements/type_depense_form.html', {'form': form})


@login_required
def type_depense_update(request, pk):
    """Modifier un type de dépense"""
    type_depense = get_object_or_404(TypeDepense, pk=pk)

    if request.method == 'POST':
        form = TypeDepenseForm(request.POST, instance=type_depense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Type de dépense modifié avec succès.')
            return redirect('paiements:type_depense_liste')
    else:
        form = TypeDepenseForm(instance=type_depense)

    context = {
        'form': form,
        'type_depense': type_depense,
    }
    return render(request, 'paiements/type_depense_form.html', context)


# =============================================================================
# VUES POUR LES DÉPENSES PROPRIÉTAIRES
# =============================================================================

@login_required
def depense_liste(request):
    """Liste des dépenses avec filtres"""
    depenses = DepenseProprietaire.objects.select_related(
        'immeuble', 'appartement', 'type_depense'
    ).all()

    # Filtres
    filtre_form = FiltreDepensesForm(request.GET)

    if filtre_form.is_valid():
        if immeuble := filtre_form.cleaned_data.get('immeuble'):
            depenses = depenses.filter(immeuble=immeuble)

        if type_depense := filtre_form.cleaned_data.get('type_depense'):
            depenses = depenses.filter(type_depense=type_depense)

        if categorie := filtre_form.cleaned_data.get('categorie'):
            depenses = depenses.filter(type_depense__categorie=categorie)

        if statut := filtre_form.cleaned_data.get('statut'):
            depenses = depenses.filter(statut=statut)

        if date_debut := filtre_form.cleaned_data.get('date_debut'):
            depenses = depenses.filter(date_depense__gte=date_debut)

        if date_fin := filtre_form.cleaned_data.get('date_fin'):
            depenses = depenses.filter(date_depense__lte=date_fin)

        if repartissable := filtre_form.cleaned_data.get('repartissable'):
            depenses = depenses.filter(repartissable=(repartissable == 'true'))

        if recherche := filtre_form.cleaned_data.get('recherche'):
            depenses = depenses.filter(
                Q(designation__icontains=recherche) |
                Q(fournisseur__icontains=recherche) |
                Q(numero_facture__icontains=recherche)
            )

    # Statistiques
    stats = depenses.aggregate(
        total=Sum('montant_ttc'),
        count=Count('id'),
        a_payer=Sum('montant_ttc', filter=Q(statut='a_payer')),
        payees=Sum('montant_ttc', filter=Q(statut='payee')),
    )

    context = {
        'depenses': depenses,
        'filtre_form': filtre_form,
        'stats': stats,
    }
    return render(request, 'paiements/depense_liste.html', context)


@login_required
def depense_detail(request, pk):
    """Détail d'une dépense"""
    depense = get_object_or_404(
        DepenseProprietaire.objects.select_related(
            'immeuble', 'appartement', 'type_depense'
        ),
        pk=pk
    )

    # Répartitions existantes
    repartitions = depense.repartitions.select_related('appartement').all()

    # Statistiques de répartition
    total_reparti = repartitions.aggregate(Sum('montant'))['montant__sum'] or Decimal('0')

    context = {
        'depense': depense,
        'repartitions': repartitions,
        'total_reparti': total_reparti,
        'reste_a_repartir': depense.montant_ttc - total_reparti,
    }
    return render(request, 'paiements/depense_detail.html', context)


@login_required
def depense_create(request):
    """Créer une dépense"""
    if request.method == 'POST':
        form = DepenseProprietaireForm(request.POST, request.FILES)
        if form.is_valid():
            depense = form.save()
            messages.success(request, 'Dépense créée avec succès.')
            return redirect('paiements:depense_detail', pk=depense.pk)
    else:
        form = DepenseProprietaireForm()

    return render(request, 'paiements/depense_form.html', {'form': form})


@login_required
def depense_update(request, pk):
    """Modifier une dépense"""
    depense = get_object_or_404(DepenseProprietaire, pk=pk)

    if request.method == 'POST':
        form = DepenseProprietaireForm(request.POST, request.FILES, instance=depense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dépense modifiée avec succès.')
            return redirect('paiements:depense_detail', pk=depense.pk)
    else:
        form = DepenseProprietaireForm(instance=depense)

    context = {
        'form': form,
        'depense': depense,
    }
    return render(request, 'paiements/depense_form.html', context)


@login_required
def depense_delete(request, pk):
    """Supprimer une dépense"""
    depense = get_object_or_404(DepenseProprietaire, pk=pk)

    if request.method == 'POST':
        depense.delete()
        messages.success(request, 'Dépense supprimée avec succès.')
        return redirect('paiements:depense_liste')

    return render(request, 'paiements/depense_confirm_delete.html', {'depense': depense})


# =============================================================================
# VUES POUR LA RÉPARTITION DES DÉPENSES
# =============================================================================

@login_required
def depense_repartir(request, pk):
    """Répartir une dépense entre appartements"""
    depense = get_object_or_404(DepenseProprietaire, pk=pk)

    if not depense.repartissable:
        messages.error(request, 'Cette dépense n\'est pas répartissable.')
        return redirect('paiements:depense_detail', pk=pk)

    if request.method == 'POST':
        form = RepartitionAutomatiqueForm(request.POST, depense=depense)
        if form.is_valid():
            # Supprimer les répartitions existantes
            depense.repartitions.all().delete()

            mode = form.cleaned_data['mode_repartition']
            tous = form.cleaned_data['tous_appartements']

            # Récupérer les appartements
            if tous:
                appartements = Appartement.objects.filter(
                    immeuble=depense.immeuble,
                )
            else:
                appartements = form.cleaned_data['appartements']

            # Calculer la répartition
            if mode == 'egalitaire':
                # ✅ Convertir en Decimal pour éviter l'erreur de type
                montant_par_appt = depense.montant_ttc / Decimal(len(appartements))
                for appt in appartements:
                    RepartitionDepense.objects.create(
                        depense=depense,
                        appartement=appt,
                        montant=montant_par_appt,
                        mode_repartition='forfait'
                    )

            elif mode == 'surface':
                # Vérifier que les appartements ont une surface
                total_surface = sum(appt.surface for appt in appartements if appt.surface is not None)
                if total_surface > 0:
                    for appt in appartements:
                        if appt.surface is not None:
                            # ✅ Convertir en Decimal pour éviter l'erreur de type
                            ratio = Decimal(str(appt.surface)) / Decimal(str(total_surface))
                            montant = ratio * depense.montant_ttc
                            RepartitionDepense.objects.create(
                                depense=depense,
                                appartement=appt,
                                montant=montant,
                                mode_repartition='surface',
                                base_calcul=appt.surface
                            )
                else:
                    messages.error(request, 'Aucun appartement n\'a de surface définie.')
                    return redirect('paiements:depense_detail', pk=pk)

            elif mode == 'milliemes':
                # Calcul par millièmes
                total_milliemes = sum(appt.milliemes for appt in appartements if appt.milliemes is not None)
                if total_milliemes > 0:
                    for appt in appartements:
                        if appt.milliemes is not None:
                            # ✅ Convertir en Decimal pour éviter l'erreur de type
                            ratio = Decimal(appt.milliemes) / Decimal(total_milliemes)
                            montant = ratio * depense.montant_ttc
                            RepartitionDepense.objects.create(
                                depense=depense,
                                appartement=appt,
                                montant=montant,
                                mode_repartition='milliemes',
                                base_calcul=appt.milliemes
                            )
                else:
                    messages.error(request, 'Aucun appartement n\'a de millièmes définis.')
                    return redirect('paiements:depense_detail', pk=pk)

            depense.repartie = True
            depense.save()

            messages.success(request, 'Dépense répartie avec succès.')
            return redirect('paiements:depense_detail', pk=pk)

    else:
        form = RepartitionAutomatiqueForm(depense=depense)

    context = {
        'form': form,
        'depense': depense,
    }
    return render(request, 'paiements/depense_repartir.html', context)





@login_required
def repartition_create(request, depense_pk):
    """Ajouter une répartition manuelle"""
    depense = get_object_or_404(DepenseProprietaire, pk=depense_pk)

    if not depense.repartissable:
        messages.error(request, 'Cette dépense n\'est pas répartissable.')
        return redirect('paiements:depense_detail', pk=depense_pk)

    # Calculer le reste à répartir
    repartitions_existantes = depense.repartitions.all()
    total_reparti = repartitions_existantes.aggregate(Sum('montant'))['montant__sum'] or Decimal('0')
    reste_a_repartir = depense.montant_ttc - total_reparti

    if request.method == 'POST':
        form = RepartitionDepenseForm(request.POST, depense=depense)
        if form.is_valid():
            repartition = form.save(commit=False)
            repartition.depense = depense
            repartition.save()

            # Mettre à jour le statut de la dépense
            total_apres = total_reparti + repartition.montant
            if total_apres >= depense.montant_ttc:
                depense.repartie = True
                depense.save()

            messages.success(request, f'Répartition ajoutée avec succès pour {repartition.appartement}.')
            return redirect('paiements:depense_detail', pk=depense_pk)
    else:
        # Pré-remplir avec le reste à répartir si c'est la dernière
        initial = {}
        if reste_a_repartir > 0:
            initial['montant'] = reste_a_repartir
        form = RepartitionDepenseForm(depense=depense, initial=initial)

    context = {
        'form': form,
        'depense': depense,
        'reste_a_repartir': reste_a_repartir,
    }
    return render(request, 'paiements/repartition_form.html', context)


@login_required
def repartition_delete(request, pk):
    """Supprimer une répartition"""
    repartition = get_object_or_404(RepartitionDepense, pk=pk)
    depense_pk = repartition.depense.pk
    depense = repartition.depense

    if request.method == 'POST':
        repartition.delete()

        # Vérifier s'il reste des répartitions
        repartitions_restantes = depense.repartitions.count()
        if repartitions_restantes == 0:
            # Plus aucune répartition, marquer comme non répartie
            depense.repartie = False
            depense.save()
            messages.info(request, 'Répartition supprimée. La dépense n\'est plus répartie.')
        else:
            # Vérifier si le total réparti est toujours égal au montant
            total_reparti = depense.repartitions.aggregate(Sum('montant'))['montant__sum'] or Decimal('0')
            if total_reparti < depense.montant_ttc:
                depense.repartie = False
                depense.save()
                messages.warning(request,
                                 f'Répartition supprimée. Il reste {depense.montant_ttc - total_reparti}€ à répartir.')
            else:
                messages.success(request, 'Répartition supprimée avec succès.')

        return redirect('paiements:depense_detail', pk=depense_pk)

    return render(request, 'paiements/repartition_confirm_delete.html', {'repartition': repartition})


# =============================================================================
# VUES AJAX
# =============================================================================

@login_required
def load_appartements(request):
    """Charger les appartements d'un immeuble (AJAX)"""
    immeuble_id = request.GET.get('immeuble_id')
    appartements = Appartement.objects.filter(immeuble_id=immeuble_id).order_by('numero')

    data = [
        {'id': appt.id, 'text': f"{appt.numero} - Étage {appt.etage}"}
        for appt in appartements
    ]

    return JsonResponse({'results': data})


@login_required
def calculer_ttc(request):
    """Calculer le TTC (AJAX)"""
    try:
        montant_ht = Decimal(request.GET.get('ht', 0))
        tva = Decimal(request.GET.get('tva', 0))
        ttc = montant_ht + tva
        return JsonResponse({'ttc': float(ttc)})
    except:
        return JsonResponse({'error': 'Calcul impossible'}, status=400)