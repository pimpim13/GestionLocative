# apps/immeubles/views.py
from django.shortcuts import render, get_object_or_404, redirect
#from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.db.models import Q, Count
from .models import Immeuble, Appartement
from .forms import ImmeubleCreateForm


class Immeuble_ListView(ListView):

    queryset = Immeuble.objects.all()
    fields = ['nom', 'adresse', 'code_postal', 'ville']
    template_name = 'immeuble/immeuble_list_2.html'
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

    template_name = 'immeuble/immeuble_detail.html'
    context_object_name = 'appartements'
    fields = ['immeuble', 'numero', 'etage', 'loue',]
    template_name = 'immeuble/appartement_list.html'
    context_object_name = 'appartement'

    def get_queryset(self):
        self.immeuble_id = self.kwargs["immeuble_id"]
        return Appartement.objects.filter(immeuble_id=self.immeuble_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['immeuble']= Immeuble.objects.get(id=self.immeuble_id)
        return context




class Appartement_ListView(ListView):
    model = Appartement
    queryset = Appartement.objects.all()

    fields = ['immeuble', 'numero', 'etage', 'loue',]
    template_name = 'immeuble/appartement_list.html'
    context_object_name = 'appartement'

class AppartementDetailView(DetailView):
    pass