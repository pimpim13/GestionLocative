# quittances/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from datetime import date, datetime

from .models import Quittance
from .forms import (
    QuittanceGenerationForm,
    QuittanceBatchForm,
    QuittanceSearchForm,
    QuittanceManuelleForm
)
from .utils import QuittanceManager
from .pdf_generator import QuittancePDFGenerator
from contrats.models import Contrats
from immeuble.models import Immeuble
from paiements.models import PaiementLocataire


def quittances_accueil(request):
    return render(request, "quittances/quittances_accueil.html")


@method_decorator(login_required, name='dispatch')
class QuittanceListView(ListView):
    """Vue liste des quittances"""
    model = Quittance
    template_name = 'quittances/quittance_list.html'
    context_object_name = 'quittances'
    paginate_by = 20

    def get_queryset(self):
        queryset = (Quittance.objects.select_related(
            'contrat__appartement__immeuble'
        ).prefetch_related(
            'contrat__locataires'
        ).order_by('-mois', '-date_generation'))

        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(contrat__locataires__nom__icontains=search) |
                Q(contrat__locataires__prenom__icontains=search) |
                Q(numero__icontains=search)
            ).distinct()  # ✅ Important pour éviter les doublons !



        immeuble_id = self.request.GET.get('immeuble')
        if immeuble_id:
            queryset = queryset.filter(
                contrat__appartement__immeuble_id=immeuble_id
            )

        mois = self.request.GET.get('mois')
        if mois:
            try:
                mois_date = datetime.strptime(mois, '%Y-%m').date()
                queryset = queryset.filter(
                    mois__year=mois_date.year,
                    mois__month=mois_date.month
                )
            except ValueError:
                pass

        envoyee = self.request.GET.get('envoyee')
        if envoyee == '1':
            queryset = queryset.filter(envoyee=True)
        elif envoyee == '0':
            queryset = queryset.filter(envoyee=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['immeubles'] = Immeuble.objects.all()
        context['search_form'] = QuittanceSearchForm(self.request.GET)
        context['current_filters'] = {
            'search': self.request.GET.get('search', ''),
            'immeuble': self.request.GET.get('immeuble', ''),
            'mois': self.request.GET.get('mois', ''),
            'envoyee': self.request.GET.get('envoyee', ''),
        }

        # Statistiques
        queryset = self.get_queryset()
        context['stats'] = {
            'total': queryset.count(),
            'envoyees': queryset.filter(envoyee=True).count(),
            'non_envoyees': queryset.filter(envoyee=False).count(),
        }

        return context


@method_decorator(login_required, name='dispatch')
class QuittanceDetailView(DetailView):
    """Vue détail d'une quittance"""
    model = Quittance
    template_name = 'quittances/quittance_detail.html'
    context_object_name = 'quittance'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ajouter le paiement associé s'il existe
        if self.object.paiement:
            context['paiement'] = self.object.paiement

        # ✅ Récupérer le locataire principal via la méthode du contrat
        locataire_principal = self.object.contrat.get_locataire_principal()
        if locataire_principal:
            context['locataire_principal'] = locataire_principal

        return context

    def get_queryset(self):
        # Optimiser pour éviter les N+1 queries
        return Quittance.objects.select_related(
            'contrat__appartement__immeuble',
            'paiement'
        ).prefetch_related(
            'contrat__locataires'
        )

@login_required
def generer_quittance_view(request, contrat_id):
    """Vue pour générer une quittance individuelle"""
    contrat = get_object_or_404(Contrats, id=contrat_id, actif=True)

    if request.method == 'POST':
        form = QuittanceGenerationForm(request.POST)
        if form.is_valid():
            mois = form.cleaned_data['mois']
            force_regeneration = form.cleaned_data.get('force_regeneration', False)

            try:
                # Vérifier s'il y a un paiement pour ce mois
                paiement = PaiementLocataire.objects.filter(
                    contrat=contrat,
                    mois=mois
                ).first()

                quittance = QuittanceManager.generer_quittance(
                    contrat=contrat,
                    mois=mois,
                    paiement=paiement,
                    force_regeneration=force_regeneration
                )

                messages.success(
                    request,
                    f'Quittance {quittance.numero} générée avec succès.'
                )
                return redirect('quittances:detail', pk=quittance.pk)

            except Exception as e:
                messages.error(
                    request,
                    f'Erreur lors de la génération de la quittance: {str(e)}'
                )
    else:
        form = QuittanceGenerationForm()

    return render(request, 'quittances/generer_quittance.html', {
        'form': form,
        'contrat': contrat
    })


@login_required
def generation_batch_view(request):
    """Vue pour la génération de quittances en lot"""

    if request.method == 'POST':
        form = QuittanceBatchForm(request.POST)
        if form.is_valid():
            mois = form.cleaned_data['mois']
            immeubles = form.cleaned_data.get('immeubles')
            uniquement_payes = form.cleaned_data.get('uniquement_payes', True)

            try:
                # Récupérer les contrats
                contrats_query = Contrats.objects.filter(
                    actif=True,
                    date_debut__lte=mois
                ).filter(
                    Q(date_fin__isnull=True) | Q(date_fin__gte=mois)
                ).select_related('appartement__immeuble').prefetch_related('locataires')

                # Filtrer par immeubles si spécifié
                if immeubles:
                    contrats_query = contrats_query.filter(
                        appartement__immeuble__in=immeubles
                    )

                # Filtrer uniquement ceux avec paiement si demandé
                if uniquement_payes:
                    contrats_avec_paiement = PaiementLocataire.objects.filter(
                        mois=mois,
                        statut__in=['recu', 'valide']
                    ).values_list('contrat_id', flat=True)

                    contrats_query = contrats_query.filter(
                        id__in=contrats_avec_paiement
                    )

                # Générer les quittances
                quittances_generees = []
                erreurs = []

                for contrat in contrats_query:
                    try:
                        paiement = PaiementLocataire.objects.filter(
                            contrat=contrat,
                            mois=mois
                        ).first()

                        quittance = QuittanceManager.generer_quittance(
                            contrat=contrat,
                            mois=mois,
                            paiement=paiement
                        )
                        quittances_generees.append(quittance)
                    except Exception as e:
                        erreurs.append({
                            'contrat': contrat,
                            'erreur': str(e)
                        })

                # Messages
                if quittances_generees:
                    messages.success(
                        request,
                        f"{len(quittances_generees)} quittance(s) générée(s) avec succès "
                        f"pour {mois.strftime('%B %Y')}."
                    )

                if erreurs:
                    messages.warning(
                        request,
                        f"{len(erreurs)} erreur(s) lors de la génération."
                    )

                return redirect('quittances:list')

            except Exception as e:
                messages.error(
                    request,
                    f'Erreur lors de la génération en lot: {str(e)}'
                )
    else:
        form = QuittanceBatchForm()

    return render(request, 'quittances/generation_batch.html', {
        'form': form
    })


@login_required
def download_pdf_view(request, pk):
    """Vue pour télécharger le PDF d'une quittance"""
    quittance = get_object_or_404(Quittance, pk=pk)

    # Régénérer le PDF si il n'existe pas
    if not quittance.fichier_pdf:
        try:
            pdf_generator = QuittancePDFGenerator(quittance)
            pdf_content = pdf_generator.generate_pdf()

            filename = f"quittance_{quittance.numero}.pdf"
            quittance.fichier_pdf.save(
                filename,
                ContentFile(pdf_content),
                save=True
            )
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du PDF: {e}")
            return redirect('quittances:detail', pk=pk)

    # Retourner le fichier
    try:
        response = FileResponse(
            quittance.fichier_pdf.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="quittance_{quittance.numero}.pdf"'
        )
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors du téléchargement: {e}")
        return redirect('quittances:detail', pk=pk)


@login_required
def preview_pdf_view(request, pk):
    """Vue pour prévisualiser le PDF dans le navigateur"""
    quittance = get_object_or_404(Quittance, pk=pk)

    if not quittance.fichier_pdf:
        try:
            pdf_generator = QuittancePDFGenerator(quittance)
            pdf_content = pdf_generator.generate_pdf()

            filename = f"quittance_{quittance.numero}.pdf"
            quittance.fichier_pdf.save(
                filename,
                ContentFile(pdf_content),
                save=True
            )
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du PDF: {e}")
            return redirect('quittances:detail', pk=pk)

    try:
        response = FileResponse(
            quittance.fichier_pdf.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = 'inline'
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de la prévisualisation: {e}")
        return redirect('quittances:detail', pk=pk)


@login_required
def marquer_envoyee_view(request, pk):
    """Marquer une quittance comme envoyée"""
    quittance = get_object_or_404(Quittance, pk=pk)

    if request.method == 'POST':
        mode_envoi = request.POST.get('mode_envoi', 'email')

        quittance.envoyee = True
        quittance.mode_envoi = mode_envoi
        quittance.date_envoi = datetime.now()
        quittance.save()

        messages.success(
            request,
            f'Quittance {quittance.numero} marquée comme envoyée par {quittance.get_mode_envoi_display()}.'
        )

    return redirect('quittances:detail', pk=pk)


@login_required
def regenerer_pdf_view(request, pk):
    """Régénérer le PDF d'une quittance"""
    quittance = get_object_or_404(Quittance, pk=pk)

    try:
        pdf_generator = QuittancePDFGenerator(quittance)
        pdf_content = pdf_generator.generate_pdf()

        filename = f"quittance_{quittance.numero}.pdf"

        # Supprimer l'ancien fichier si existe
        if quittance.fichier_pdf:
            quittance.fichier_pdf.delete(save=False)

        # Sauvegarder le nouveau
        quittance.fichier_pdf.save(
            filename,
            ContentFile(pdf_content),
            save=True
        )

        messages.success(
            request,
            f'PDF de la quittance {quittance.numero} régénéré avec succès.'
        )
    except Exception as e:
        messages.error(
            request,
            f'Erreur lors de la régénération du PDF: {str(e)}'
        )

    return redirect('quittances:detail', pk=pk)


@method_decorator(login_required, name='dispatch')
class QuittanceCreateView(LoginRequiredMixin, CreateView):
    """Créer une quittance manuellement"""
    model = Quittance
    form_class = QuittanceManuelleForm
    template_name = 'quittances/quittance_form.html'

    def get_initial(self):
        initial = super().get_initial()
        contrat_id = self.kwargs.get('contrat_id')
        if contrat_id:
            initial['contrat'] = contrat_id
        return initial

    def form_valid(self, form):
        quittance = form.save(commit=False)

        # Générer le PDF
        try:
            pdf_generator = QuittancePDFGenerator(quittance)
            pdf_content = pdf_generator.generate_pdf()

            filename = f"quittance_{quittance.numero}.pdf"
            quittance.fichier_pdf.save(
                filename,
                ContentFile(pdf_content),
                save=False
            )
        except Exception as e:
            messages.warning(
                self.request,
                f'Quittance créée mais erreur PDF: {e}'
            )

        quittance.save()

        messages.success(
            self.request,
            f'Quittance {quittance.numero} créée avec succès.'
        )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('quittances:detail', kwargs={'pk': self.object.pk})


@method_decorator(login_required, name='dispatch')
class QuittanceUpdateView(LoginRequiredMixin, UpdateView):
    """Modifier une quittance"""
    model = Quittance
    form_class = QuittanceManuelleForm
    template_name = 'quittances/quittance_form.html'



    def form_valid(self, form):
        messages.success(
            self.request,
            f'Quittance {self.object.numero} modifiée avec succès.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('quittances:detail', kwargs={'pk': self.object.pk})
