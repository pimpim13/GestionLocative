from django.contrib import admin
from django.urls import path, include
from .views import home, DashboardView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/admin/', DashboardView.as_view(), name='dashboard_admin'),



    path('accounts/', include('accounts.urls')),
    path('immeuble/', include('immeuble.urls')),
    path('persons/', include('persons.urls')),
    path('contrats/', include('contrats.urls')),
    path('paiements/', include('paiements.urls')),
    path('quittances/', include('quittances.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
