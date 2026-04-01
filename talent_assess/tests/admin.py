from django.contrib import admin
from .models import Test

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['_id', 'test_id', 'candidate', 'experience_level', 'status', 'percentage', 'passed', 'created_at']
    list_filter = ['status', 'passed', 'experience_level', 'created_at']
    search_fields = ['test_id', 'candidate__email']
    raw_id_fields = ['candidate', 'template']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('test_id', 'candidate', 'template')
        }),
        ('Test Configuration', {
            'fields': ('experience_level', 'selected_technologies', 'duration_minutes')
        }),
        ('Questions', {
            'fields': ('aptitude_questions', 'technical_questions'),
            'classes': ('collapse',)
        }),
        ('Answers', {
            'fields': ('answers',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'start_time', 'end_time')
        }),
        ('Results', {
            'fields': ('total_marks', 'obtained_marks', 'percentage', 'passed')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['test_id', 'created_at']
    
    actions = ['recalculate_results']
    
    def recalculate_results(self, request, queryset):
        for test in queryset:
            test.calculate_results()
        self.message_user(request, f"{queryset.count()} tests recalculated")
    recalculate_results.short_description = "Recalculate results for selected tests"