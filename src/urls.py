#src/urls.py

from django.contrib import admin
from django.urls import path, include
from .views import home, DashboardView
from .authentication import create_user_view
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views
from .authentication import custom_login_view, custom_logout_view, profile_view

app_name = 'src'

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

    path('users/create/', create_user_view, name='create_user'),

    # Authentification
    path('login/', custom_login_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),

    # Changement de mot de passe
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
