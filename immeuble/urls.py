# apps/immeubles/urls.py
from django.urls import path
from .views import Immeuble_ListView, Immeuble_CreateView, ImmeubleDetail_ListView, AppartementListView, \
    AppartementDetailView, Immeuble_UpdateView, Appartement_CreateView, Appartement_UpdateView
from .views import immeuble_delete_item, Appartement_delete_item

app_name = 'immeuble'

urlpatterns = [
    # Immeubles
    path('',Immeuble_ListView.as_view(), name='list_immeuble'),
    path('<int:pk>/', ImmeubleDetail_ListView.as_view(), name='immeuble_detail'),
    path('create/', Immeuble_CreateView.as_view(), name='create_immeuble'),
    path('immeuble/update/<int:pk>/', Immeuble_UpdateView.as_view(), name='update_immeuble'),
    path('immeuble/delete/<str:nom>/', immeuble_delete_item, name='delete_immeuble'),

    path('appartements/', AppartementListView.as_view(), name='appartement_list'),
    path('appartements/create/', Appartement_CreateView.as_view(), name='create_appartement'),
    path('appartements/delete/<int:pk>', Appartement_delete_item, name='delete_appartement'),
    path('appartements/update/<int:pk>', Appartement_UpdateView.as_view(), name='update_appartement'),


    # path('<int:pk>/edit/', views.ImmeubleUpdateView.as_view(), name='update'),

]
