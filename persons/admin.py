from django.contrib import admin

from persons.models import Proprietaires, Locataires


@admin.register(Proprietaires)
class Proprietaires(admin.ModelAdmin):
    list_display = ('raison_sociale', 'nom', 'prenom', 'email', 'telephone', 'actif')


@admin.register(Locataires)
class Locataires(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'telephone', 'notes', 'actif')