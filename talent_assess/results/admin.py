from django.contrib import admin
from .models import Result

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['_id', 'test', 'candidate', 'obtained_marks', 'percentage', 'passed', 'evaluated_at']
    list_filter = ['passed', 'evaluated_at']
    search_fields = ['test__test_id', 'candidate__email']
    raw_id_fields = ['test', 'candidate']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('test', 'candidate')
        }),
        ('Summary', {
            'fields': ('total_questions', 'attempted', 'correct', 'wrong', 'skipped')
        }),
        ('Marks', {
            'fields': ('total_marks', 'obtained_marks', 'percentage', 'passed')
        }),
        ('Detailed Stats', {
            'fields': ('category_wise', 'technology_wise', 'question_results'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('evaluated_at',)
        }),
    )
    
    readonly_fields = ['evaluated_at']