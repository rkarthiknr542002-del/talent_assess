from django.contrib import admin
from .models import Question

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['_id', 'question_text_preview', 'level', 'category', 'technology', 'question_type', 'marks', 'is_active']
    list_filter = ['level', 'category', 'technology', 'question_type', 'is_active', 'created_at']
    search_fields = ['question_text', 'explanation']
    raw_id_fields = ['created_by']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('level', 'category', 'technology', 'question_type', 'language')
        }),
        ('Question Content', {
            'fields': ('question_text', 'options', 'correct_answer', 'marks', 'explanation')
        }),
        ('Timing', {
            'fields': ('time_to_solve_seconds',)
        }),
        ('Statistics', {
            'fields': ('times_used', 'correct_count', 'wrong_count'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'times_used', 'correct_count', 'wrong_count']
    
    def question_text_preview(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_preview.short_description = 'Question'