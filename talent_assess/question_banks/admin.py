from django.contrib import admin
from .models import QuestionBank

@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['_id', 'name', 'level', 'category', 'total_questions', 'is_active', 'created_at']
    list_filter = ['level', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    raw_id_fields = ['created_by']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Classification', {
            'fields': ('level', 'category', 'technologies')
        }),
        ('Questions', {
            'fields': ('questions',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def total_questions(self, obj):
        return obj.total_questions
    total_questions.short_description = 'Total Questions'