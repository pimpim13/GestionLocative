# apps/immeubles/views.py
from django.shortcuts import render, get_object_or_404, redirect
#from django.contrib.auth.decorators import login_required
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
    #fields = ['nom', 'adresse', 'code_postal', 'ville']
    template_name = 'immeuble/immeuble_create.html'
    success_url = reverse_lazy('immeuble:list_immeuble')
    context_object_name = 'immeubles'


class Immeuble_UpdateView(UpdateView):
    model = Immeuble
    form_class = ImmeubleCreateForm
    template_name = 'immeuble/immeuble_update.html'
    success_url = reverse_lazy('immeuble:list_immeuble')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['immeubles'] = Immeuble.objects.all()
        return context

def immeuble_delete_item(request, nom):
    Immeuble.objects.get(nom=nom).delete()
    return redirect('immeuble:list_immeuble')


class ImmeubleDetail_ListView(ListView):

    fields = ['immeuble', 'numero', 'etage', 'loue',]
    template_name = 'immeuble/appartement_list.html'
    context_object_name = 'appartements'

    def get_queryset(self):
        immeuble_id = self.kwargs.get('pk')
        queryset = Appartement.objects.filter(immeuble__id=immeuble_id)
        return queryset

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        immeuble_id = self.kwargs.get('pk')
        context['immeuble'] = Immeuble.objects.get(pk=immeuble_id)
        return context


class Appartement_CreateView(CreateView):
    model = Appartement
    form_class = AppartementForm
    #fields = ['nom', 'adresse', 'code_postal', 'ville']
    template_name = 'immeuble/appartement_create.html'
    success_url = reverse_lazy('immeuble:list_immeuble')
    context_object_name = 'appartement'


class Appartement_UpdateView(UpdateView):
    model = Appartement
    form_class = AppartementForm
    #fields = ['nom', 'adresse', 'code_postal', 'ville']
    template_name = 'immeuble/appartement_update.html'
    success_url = reverse_lazy('immeuble:list_immeuble')
    context_object_name = 'appartement'

def Appartement_delete_item(request, pk):
    Appartement.objects.get(id=pk).delete()
    return redirect('immeuble:list_immeuble')


class AppartementListView(ListView):
    model = Appartement
    fields = ['immeuble', 'numero', 'etage', 'loue',]
    template_name = 'immeuble/appartement_list.html'
    context_object_name = 'appartements'

    def get_queryset(self):
        queryset = Appartement.objects.select_related(
            'immeuble'
        )
        immeuble_id = self.request.GET.get('immeuble', '')
        if immeuble_id:
            queryset = queryset.filter(immeuble_id=immeuble_id)
        else:
            queryset = Appartement.objects.all()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filters'] = {
                 'immeuble' : self.request.GET.get('immeuble', '')
        }




class AppartementDetailView(DetailView):

    form = AppartementForm
    template_name = 'immeuble/appartement_create.html'
    success_url = reverse_lazy('immeuble:immeuble_detail')


    def get_queryset(self):
        self.pk = self.kwargs["pk"]
        return Appartement.objects.filter(id=self.pk)