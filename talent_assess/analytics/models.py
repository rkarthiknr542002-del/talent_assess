from django.db import models
from djongo import models as djongo_models
from datetime import datetime, date

class Analytics(models.Model):
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    date = models.DateField(default=date.today, unique=True)
    
    # Daily stats
    total_tests_taken = models.IntegerField(default=0)
    total_candidates = models.IntegerField(default=0)
    pass_count = models.IntegerField(default=0)
    fail_count = models.IntegerField(default=0)
    
    # Detailed stats
    level_wise_stats = models.JSONField(null=True, blank=True, default=dict)  
    technology_wise_stats = models.JSONField(null=True, blank=True, default=dict)  
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics'
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"Analytics for {self.date}"
    
    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)