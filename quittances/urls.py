# quittances/urls.py

from django.urls import path
from . import views

app_name = 'quittances'

urlpatterns = [
    # Liste et recherche
    path('accueil/', views.quittances_accueil, name='quittances_accueil'),
    path('list/', views.QuittanceListView.as_view(), name='list'),
    path('<int:pk>/', views.QuittanceDetailView.as_view(), name='detail'),

    # Génération
    path('generer/<int:contrat_id>/', views.generer_quittance_view, name='generer'),
    path('generation-batch/', views.generation_batch_view, name='generation_batch'),

    # PDF
    path('<int:pk>/download/', views.download_pdf_view, name='download_pdf'),
    path('<int:pk>/preview/', views.preview_pdf_view, name='preview_pdf'),
    path('<int:pk>/regenerer/', views.regenerer_pdf_view, name='regenerer_pdf'),

    # Actions
    path('<int:pk>/marquer-envoyee/', views.marquer_envoyee_view, name='marquer_envoyee'),

    # CRUD manuel
    path('creer/', views.QuittanceCreateView.as_view(), name='create'),
    path('creer/<int:contrat_id>/', views.QuittanceCreateView.as_view(), name='create_contrat'),
    path('<int:pk>/modifier/', views.QuittanceUpdateView.as_view(), name='update'),
]
