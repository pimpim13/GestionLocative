# apps/immeubles/views.py
from django.shortcuts import render, get_object_or_404, redirect
#from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
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
