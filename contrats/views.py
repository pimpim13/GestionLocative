from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from contrats.models import Contrats
from .forms  import ContratForm


# Create your views here.


class Contrats_ListView(ListView):
    model = Contrats
    fields = ['raison_sociale', 'nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'contrats/contrat_list.html'
    context_object_name = 'contrats'

class Contrats_CreateView(CreateView):
    model = Contrats
    form_class = ContratForm
    template_name = 'contrats/contrat_create.html'
    success_url = reverse_lazy('contrats:contrats_list')
    context_object_name = 'contrat'

class Contrats_UpdateView(UpdateView):
    model = Contrats
    form_class = ContratForm
    template_name = 'contrats/contrat_update.html'
    success_url = reverse_lazy('contrats:contrats_list')
    context_object_name = 'contrat'


def contrat_delete_item(request, pk):
    Contrats.objects.get(id=pk).delete()
    return redirect('contrats:contrats_list')


def contrats_accueil(request):
    return redirect('src:home')
