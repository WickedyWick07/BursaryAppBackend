# bursaryDataMiner/admin.py
from django.contrib import admin
from .models import Bursary, BursaryEmbedding, UserBursaryMatch

@admin.register(Bursary)
class BursaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'date_found')
    
@admin.register(BursaryEmbedding)
class BursaryEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('bursary', 'updated_at')
    readonly_fields = ('vector',)  # optional, prevents accidental edits
