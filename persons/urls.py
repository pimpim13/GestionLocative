# persons/urs.py

from django.urls import path

from persons.views import Proprietaires_ListView, Proprietaires_CreateView, Proprietaires_UpdateView, persons_accueil, \
    Locataires_ListView, Locataires_UpdateView, Locataires_CreateView, Locataires_DetailView



app_name = 'persons'

urlpatterns = [
    # Persons
    path('accueil', persons_accueil, name='persons_accueil'),
    path('proprietaires/',Proprietaires_ListView.as_view(), name='proprietaires_list'),
    path('proprietaires/create/',Proprietaires_CreateView.as_view(), name='proprietaire_create'),
    path('proprietaire/update/<int:pk>/',Proprietaires_UpdateView.as_view(), name='proprietaire_update'),
    path('locataires/', Locataires_ListView.as_view(), name='locataires_list'),
    path('locataires/create/', Locataires_CreateView.as_view(), name='locataire_create'),
    path('locataires/update/<int:pk>/', Locataires_UpdateView.as_view(), name='locataire_update'),
    path('locataires/detail/<int:pk>/', Locataires_DetailView.as_view(), name='locataire_detail')
    ]