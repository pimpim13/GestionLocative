# apps/immeubles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .models import Immeuble, Appartement
from .forms import ImmeubleCreateForm, AppartementForm


class Immeuble_ListView(ListView):
    model = Immeuble
    fields = ['nom', 'adresse', 'code_postal', 'ville']
    template_name = 'immeuble/immeuble_list.html'
    context_object_name = 'immeubles'


class Immeuble_CreateView(CreateView):
    model = Immeuble
    form_class = ImmeubleCreateForm
    template_name = 'immeuble/immeuble_create.html'
    success_url = reverse_lazy('immeuble:list_immeuble')
    context_object_name = 'immeubles'


class Immeuble_UpdateView(UpdateView):
    model = Immeuble
    form_class = ImmeubleCreateForm
    template_name = 'immeuble/immeuble_update.html'
    success_url = reverse_lazy('immeuble:list_immeuble')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['immeubles'] = Immeuble.objects.all()
        return context


def immeuble_delete_item(request, nom):
    Immeuble.objects.get(nom=nom).delete()
    return redirect('immeuble:list_immeuble')


class ImmeubleDetail_ListView(ListView):
    fields = ['immeuble', 'numero', 'etage', 'loue']
    template_name = 'immeuble/appartement_list.html'
    context_object_name = 'appartements'

    def get_queryset(self):
        immeuble_id = self.kwargs.get('pk')
        queryset = Appartement.objects.filter(immeuble__id=immeuble_id).select_related('immeuble', 'proprietaire')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        immeuble_id = self.kwargs.get('pk')
        context['immeuble'] = Immeuble.objects.get(pk=immeuble_id)
        return context


class Appartement_CreateView(CreateView):
    model = Appartement
    form_class = AppartementForm
    template_name = 'immeuble/appartement_create.html'
    success_url = reverse_lazy('immeuble:list_immeuble')
    context_object_name = 'appartement'


class Appartement_UpdateView(UpdateView):
    model = Appartement
    form_class = AppartementForm
    template_name = 'immeuble/appartement_update.html'
    success_url = reverse_lazy('immeuble:list_immeuble')
    context_object_name = 'appartement'


def Appartement_delete_item(request, pk):
    Appartement.objects.get(id=pk).delete()
    return redirect('immeuble:list_immeuble')


class AppartementListView(ListView):
    model = Appartement  # ✅ Ajout du model
    fields = ['immeuble', 'numero', 'etage', ] #'loue'
    template_name = 'immeuble/appartement_list.html'
    context_object_name = 'appartements'

    def get_queryset(self):
        """Récupère tous les appartements avec filtrage optionnel par immeuble"""
        queryset = Appartement.objects.select_related('immeuble', 'proprietaire')

        # Filtrage par immeuble si paramètre fourni
        immeuble_id = self.request.GET.get('immeuble', '')
        if immeuble_id:
            queryset = queryset.filter(immeuble_id=immeuble_id)

        return queryset.order_by('immeuble__nom', 'numero')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ajouter la liste des immeubles pour le filtre
        context['immeubles'] = Immeuble.objects.all().order_by('nom')

        # Récupérer l'immeuble_id et le convertir en int si présent
        immeuble_id = self.request.GET.get('immeuble', '')

        context['current_filters'] = {
            'immeuble': int(immeuble_id) if immeuble_id else None  # ✅ Conversion en int
        }

        # Ajouter l'immeuble sélectionné si filtre actif
        if immeuble_id:
            try:
                context['immeuble'] = Immeuble.objects.get(pk=immeuble_id)
                context['immeuble_selected_id'] = int(immeuble_id)  # ✅ ID en int
            except (Immeuble.DoesNotExist, ValueError):
                context['immeuble'] = None
                context['immeuble_selected_id'] = None

        return context


class AppartementDetailView(DetailView):
    model = Appartement
    form_class = AppartementForm
    template_name = 'immeuble/appartement_detail.html'
    context_object_name = 'appartement'

    def get_queryset(self):
        return Appartement.objects.select_related('immeuble', 'proprietaire')