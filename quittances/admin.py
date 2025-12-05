from django.contrib import admin

from quittances.models import Quittance


@admin.register(Quittance)
class Quittance (admin.ModelAdmin):
    list_display = ('mois', 'loyer')
