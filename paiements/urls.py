# paiements/urls.py

from django.urls import path
# from .views import (
#     paiements_accueil,
#     PaiementListView,  # NOUVEAU : Vue principale pour paiement_list.html
#     PaiementsContrats_list,
#     PaiementCreateView,
#     PaiementsLocataire_List,
#     PaiementUpdateView,
#     paiement_delete_item,
#     paiement_valider
# )
from . import views

app_name = 'paiements'

urlpatterns = [
    # Page d'accueil
    path('accueil/', views.paiements_accueil, name='paiements_accueil'),

    # Liste globale de tous les paiements (NOUVEAU)
    path('', views.PaiementListView.as_view(), name='paiement_list'),

    # Liste des contrats avec paiements
    path('contrats/', views.PaiementsContrats_list.as_view(), name='paiements_contrats_list'),

    # Liste des paiements d'un contrat spécifique
    path('contrat/<int:contrat_id>/', views.PaiementsLocataire_List.as_view(), name='paiements_locataires_list'),

    # Création et modification

    path('create/', views.PaiementCreateView.as_view(), name='paiement_create_'),
    path('create/<int:contrat_id>/', views.PaiementCreateView.as_view(), name='paiement_create'),
    path('update/<int:pk>/', views.PaiementUpdateView.as_view(), name='paiement_update'),

    # Actions
    path('delete/<int:pk>/', views.paiement_delete_item, name='paiement_delete'),
    path('valider/<int:pk>/',views.paiement_valider, name='paiement_valider'),

    # Types de dépenses
    path('types/', views.type_depense_liste, name='type_depense_liste'),
    path('types/nouveau/', views.type_depense_create, name='type_depense_create'),
    path('types/<int:pk>/modifier/', views.type_depense_update, name='type_depense_update'),

    # Dépenses propriétaires
    path('depenses/', views.depense_liste, name='depense_liste'),
    path('depenses/nouvelle/', views.depense_create, name='depense_create'),
    path('depenses/<int:pk>/', views.depense_detail, name='depense_detail'),
    path('depenses/<int:pk>/modifier/', views.depense_update, name='depense_update'),
    path('depenses/<int:pk>/supprimer/', views.depense_delete, name='depense_delete'),

    # Répartitions
    path('depenses/<int:pk>/repartir/', views.depense_repartir, name='depense_repartir'),
    path('depenses/<int:depense_pk>/repartition/nouvelle/', views.repartition_create, name='repartition_create'),
    path('repartitions/<int:pk>/supprimer/', views.repartition_delete, name='repartition_delete'),

    # AJAX
    path('ajax/appartements/', views.load_appartements, name='load_appartements'),
    path('ajax/calculer-ttc/', views.calculer_ttc, name='calculer_ttc'),

]