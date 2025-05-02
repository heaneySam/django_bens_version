from django.contrib import admin
from .models import Risk

@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_by',)
