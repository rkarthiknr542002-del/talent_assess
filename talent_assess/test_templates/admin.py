from django.contrib import admin
from .models import TestTemplate

@admin.register(TestTemplate)
class TestTemplateAdmin(admin.ModelAdmin):
    list_display = ['_id', 'name', 'experience_level', 'num_aptitude', 'num_technical_per_tech', 'is_active', 'created_at']
    list_filter = ['experience_level', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    raw_id_fields = ['created_by']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Configuration', {
            'fields': ('experience_level', 'technologies', 'num_aptitude', 'num_technical_per_tech')
        }),
        ('Test Settings', {
            'fields': ('duration_minutes', 'pass_percentage')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def total_questions_display(self, obj):
        return obj.total_questions
    total_questions_display.short_description = 'Total Questions'