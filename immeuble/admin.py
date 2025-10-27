from django.contrib import admin
from immeuble.models import Immeuble, Appartement


@admin.register(Immeuble)
class Immeuble(admin.ModelAdmin):
    list_display = ('nom', 'adresse', 'ville', 'code_postal' ,'charges_communes_annuelles')


@admin.register(Appartement)
class Appartement(admin.ModelAdmin):
    list_display = ('immeuble', 'numero', 'etage', 'proprietaire', 'loue' )