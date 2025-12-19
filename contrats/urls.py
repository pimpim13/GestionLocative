# contrats/urls.py
from django.urls import path
from .views import (
    Contrats_ListView, Contrats_CreateView, Contrats_UpdateView,
    contrats_accueil, contrat_delete_item,
    # Nouvelles vues pour locataires
    contrat_locataires_list, ajouter_locataire_contrat,
    creer_et_ajouter_locataire, retirer_locataire_contrat,
    definir_principal, modifier_ordre_locataires
)

app_name = 'contrats'

urlpatterns = [
    # Contrats
    path('accueil', contrats_accueil, name='contrats_accueil'),
    path('list/', Contrats_ListView.as_view(), name='contrats_list'),
    path('create/', Contrats_CreateView.as_view(), name='contrat_create'),
    path('update/<int:pk>/', Contrats_UpdateView.as_view(), name='contrat_update'),
    path('delete/<int:pk>/', contrat_delete_item, name='contrat_delete'),

    # Gestion des locataires d'un contrat
    path('<int:contrat_id>/locataires/', contrat_locataires_list, name='contrat_locataires'),
    path('<int:contrat_id>/locataires/ajouter/', ajouter_locataire_contrat, name='ajouter_locataire'),
    path('<int:contrat_id>/locataires/creer/', creer_et_ajouter_locataire, name='creer_locataire'),
    path('<int:contrat_id>/locataires/<int:relation_id>/retirer/', retirer_locataire_contrat, name='retirer_locataire'),
    path('<int:contrat_id>/locataires/<int:relation_id>/principal/', definir_principal, name='definir_principal'),
    path('<int:contrat_id>/locataires/ordre/', modifier_ordre_locataires, name='modifier_ordre'),
]