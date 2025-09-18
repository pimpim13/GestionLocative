from django.contrib import admin
from immeuble.models import Immeuble, Appartement


@admin.register(Immeuble)
class CustomUser(admin.ModelAdmin):
    list_display = ('nom', 'adresse', 'code_postal' ,'ville')


@admin.register(Appartement)
class CustomUser(admin.ModelAdmin):
    list_display = ('immeuble', 'numero', 'etage' ,'loue')