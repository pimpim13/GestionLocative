# apps/immeubles/urls.py
from django.urls import path
from .views import Immeuble_ListView, Immeuble_CreateView

app_name = 'immeuble'

urlpatterns = [
    # Immeubles
    # path('', ImmeubleListView.as_view(), name='list'),
    path('list/',Immeuble_ListView.as_view(), name='list_immeuble'),
    # path('<int:pk>/', views.ImmeubleDetailView.as_view(), name='detail'),
    path('create/', Immeuble_CreateView.as_view(), name='create_immeuble'),
    # path('<int:pk>/edit/', views.ImmeubleUpdateView.as_view(), name='update'),

    # Appartements
    # path('appartements/', views.AppartementListView.as_view(), name='appartement_list'),
    # path('appartements/<int:pk>/', views.AppartementDetailView.as_view(), name='appartement_detail'),
    # path('appartements/create/', views.AppartementCreateView.as_view(), name='appartement_create'),
    # path('appartements/<int:pk>/edit/', views.AppartementUpdateView.as_view(), name='appartement_update'),
]