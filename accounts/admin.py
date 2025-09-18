from django.contrib import admin
from accounts.models import CustomUser


@admin.register(CustomUser)
class CustomUser(admin.ModelAdmin):
    list_display = ('email', 'is_admin', 'last_login')
