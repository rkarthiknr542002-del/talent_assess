from django.db import models
from djongo import models as djongo_models
from accounts.models import User
from tests.models import Test
from datetime import datetime

class Result(models.Model):
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    test = djongo_models.OneToOneField(Test, on_delete=models.CASCADE, related_name='result', db_column='test')
    candidate = djongo_models.ForeignKey(User, on_delete=models.CASCADE, related_name='results', db_column='candidate')
    
    # Summary
    total_questions = models.IntegerField(null=True, blank=True)
    attempted = models.IntegerField(default=0)
    correct = models.IntegerField(default=0)
    wrong = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    
    # Marks
    total_marks = models.IntegerField(null=True, blank=True)
    obtained_marks = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    
    # Detailed stats
    category_wise = models.JSONField(null=True, blank=True)  # {"aptitude": {"total":10,"correct":7}, "technical": {...}}
    technology_wise = models.JSONField(null=True, blank=True)  # {"python": {"total":5,"correct":4}, "react": {...}}
    question_results = models.JSONField(null=True, blank=True)  # [{id, text, selected, correct, marks_obtained}]
    
    # Metadata
    evaluated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'results'
        indexes = [
            models.Index(fields=['test']),
            models.Index(fields=['candidate']),
            models.Index(fields=['-evaluated_at']),
        ]
    
    def __str__(self):
        return f"Result for {self.test.test_id}"
    
    def save(self, *args, **kwargs):
        if not self.evaluated_at:
            self.evaluated_at = datetime.now()
        super().save(*args, **kwargs)