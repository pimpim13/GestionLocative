# paiements/urls.py

from django.urls import path
from .views import (
    paiements_accueil,
    PaiementListView,  # NOUVEAU : Vue principale pour paiement_list.html
    PaiementsContrats_list,
    PaiementCreateView,
    PaiementsLocataire_List,
    PaiementUpdateView,
    paiement_delete_item,
    paiement_valider
)

app_name = 'paiements'

urlpatterns = [
    # Page d'accueil
    path('accueil/', paiements_accueil, name='paiements_accueil'),

    # Liste globale de tous les paiements (NOUVEAU)
    path('', PaiementListView.as_view(), name='paiement_list'),

    # Liste des contrats avec paiements
    path('contrats/', PaiementsContrats_list.as_view(), name='paiements_contrats_list'),

    # Liste des paiements d'un contrat spécifique
    path('contrat/<int:contrat_id>/', PaiementsLocataire_List.as_view(), name='paiements_locataires_list'),

    # Création et modification

    path('create/', PaiementCreateView.as_view(), name='paiement_create_'),
    path('create/<int:contrat_id>/', PaiementCreateView.as_view(), name='paiement_create'),
    path('update/<int:pk>/', PaiementUpdateView.as_view(), name='paiement_update'),

    # Actions
    path('delete/<int:pk>/', paiement_delete_item, name='paiement_delete'),
    path('valider/<int:pk>/', paiement_valider, name='paiement_valider'),
]