from django.contrib import admin
from .models import Appt, Pay

@admin.register(Appt)
class Appt(admin.ModelAdmin):
    list_display = ('nom', 'loyer')

@admin.register(Pay)
class Appt(admin.ModelAdmin):
    list_display = ('num', 'loyer')