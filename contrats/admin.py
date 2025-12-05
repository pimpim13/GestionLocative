from django.contrib import admin

from contrats.models import Contrats


@admin.register(Contrats)
class Contrats(admin.ModelAdmin):
    list_display = ['locataire', 'jour_echeance']
