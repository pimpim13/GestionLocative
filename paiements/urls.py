from django.urls import path
from .views import paiements_accueil, PaiementsContrats_list, PaiementCreateView, PaiementsLocataire_List

app_name = 'paiements'

urlpatterns = [
    # Persons
    path('accueil/', paiements_accueil, name='paiements_accueil'),
    path('contrats_list/', PaiementsContrats_list.as_view(), name='paiements_contrats_list'),
    path('locataire_list/<int:contrat_id>', PaiementsLocataire_List.as_view(), name='paiements_locataires_list'),
    path('create/<int:contrat_id>', PaiementCreateView.as_view(), name='paiement_create'),
    ]
