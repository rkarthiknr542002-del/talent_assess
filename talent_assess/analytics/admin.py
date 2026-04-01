from django.contrib import admin
from .models import Analytics

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ['_id', 'date', 'total_tests_taken', 'total_candidates', 'pass_count', 'fail_count']
    list_filter = ['date']
    search_fields = ['date']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Date Info', {
            'fields': ('date',)
        }),
        ('Daily Stats', {
            'fields': ('total_tests_taken', 'total_candidates', 'pass_count', 'fail_count')
        }),
        ('Detailed Stats', {
            'fields': ('level_wise_stats', 'technology_wise_stats'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )