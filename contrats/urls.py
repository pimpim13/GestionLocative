# contrats/urls.py

from django.urls import path

from persons.urls import urlpatterns
from contrats.views import (Contrats_ListView, Contrats_CreateView, Contrats_UpdateView,
                            contrats_accueil, contrat_delete_item)




app_name = 'contrats'

urlpatterns = [
    # Contrats
    path('accueil', contrats_accueil, name='contrats_accueil'),
    path('list/',Contrats_ListView.as_view(), name='contrats_list'),
    path('create/',Contrats_CreateView.as_view(), name='contrat_create'),
    path('update/<int:pk>/',Contrats_UpdateView.as_view(), name='contrat_update'),
    path('delete/<int:pk>/',contrat_delete_item, name='contrat_delete'),
    ]