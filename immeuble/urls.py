# apps/immeubles/urls.py
from django.urls import path
from .views import Immeuble_ListView, Immeuble_CreateView, ImmeubleDetail_ListView, Appartement_ListView, \
    AppartementDetailView, Immeuble_UpdateView
from .views import immeuble_delete_item

app_name = 'immeuble'

urlpatterns = [
    # Immeubles
    path('',Immeuble_ListView.as_view(), name='list_immeuble'),
    path('immeuble/update/<int:pk>', Immeuble_UpdateView.as_view(), name='update_immeuble'),
    path('immeuble/delete/<str:nom>', immeuble_delete_item, name='delete_immeuble'),
    path('<int:immeuble_id>/appartements/', ImmeubleDetail_ListView.as_view(), name='immeuble_detail'),
    path('create/', Immeuble_CreateView.as_view(), name='create_immeuble'),
    # path('<int:pk>/edit/', views.ImmeubleUpdateView.as_view(), name='update'),

]
