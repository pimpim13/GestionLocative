#paiments/urls.py

from django.urls import path
from .views import paiements_accueil, PaiementsContrats_list, PaiementCreateView, PaiementsLocataire_List, \
    PaiementUpdateView, paiement_delete_item

app_name = 'paiements'

urlpatterns = [
    # Persons
    path('accueil/', paiements_accueil, name='paiements_accueil'),
    path('contrats_list/', PaiementsContrats_list.as_view(), name='paiements_contrats_list'),
    path('locataire_list/<int:contrat_id>', PaiementsLocataire_List.as_view(), name='paiements_locataires_list'),
    path('create/<int:contrat_id>', PaiementCreateView.as_view(), name='paiement_create'),
    path('update/<int:pk>', PaiementUpdateView.as_view(), name='paiement_update'),
    path('delete/<int:pk>', paiement_delete_item, name='paiement_delete'),
    ]
