from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from persons.models import Proprietaires, Locataires
from persons.forms import ProprietaireForm, LocataireForm


def persons_accueil(request):
    return render(request, "persons/persons_accueil.html")


class Proprietaires_ListView(ListView):
    model=Proprietaires
    fields = ['raison_sociale', 'nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'persons/proprietaires_list.html'
    context_object_name = 'proprietaires'


class Proprietaires_CreateView(CreateView):
    model=Proprietaires
    form_class = ProprietaireForm
    template_name = 'persons/proprietaire_create.html'
    success_url = reverse_lazy('persons:proprietaires_list')
    context_object_name = 'proprietaire'


class Proprietaires_UpdateView(UpdateView):
    model=Proprietaires
    form_class = ProprietaireForm
    template_name = 'persons/proprietaire_update.html'
    success_url = reverse_lazy('persons:proprietaires_list')


class Locataires_ListView(ListView):
    model=Locataires
    fields = ['nom', 'prenom', 'email', 'telephone', 'actif']
    template_name = 'persons/locataires_list.html'
    context_object_name = 'locat'


class Locataires_CreateView(CreateView):
    model=Locataires
    form_class = LocataireForm
    template_name = 'persons/locataire_create.html'
    success_url = reverse_lazy('persons:locataires_list')
    context_object_name = 'locataires'


class Locataires_UpdateView(UpdateView):
    model = Locataires
    form_class = LocataireForm
    template_name = 'persons/locataire_update.html'
    success_url = reverse_lazy('persons:locataires_list')

