from django.db import models
from djongo import models as djongo_models
from accounts.models import User
from datetime import datetime

class TestTemplate(models.Model):
    LEVEL_CHOICES = [
        ('intern', 'Intern'),
        ('junior', 'Junior'),
        ('mid', 'Mid'),
        ('senior', 'Senior'),
    ]
    
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    experience_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    technologies = models.JSONField(null=True, blank=True)  
    
    # Question counts
    num_aptitude = models.IntegerField(default=5)
    num_technical_per_tech = models.IntegerField(default=10)
    
    # Test settings
    duration_minutes = models.IntegerField(default=30)
    pass_percentage = models.IntegerField(default=60)
    
    # Metadata
    created_by = djongo_models.ForeignKey(User, on_delete=models.CASCADE, db_column='created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'test_templates'
        indexes = [
            models.Index(fields=['experience_level']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    

    @property
    def total_questions(self):
        """Calculate total questions in template"""
        num_aptitude = self.num_aptitude or 0
        
        if self.technologies is None:
            tech_count = 0
        else:
            tech_count = len(self.technologies)
        
        num_technical_per_tech = self.num_technical_per_tech or 0
        
        return num_aptitude + (tech_count * num_technical_per_tech)


    @property
    def total_marks(self):
        """Calculate total marks"""
        num_aptitude = self.num_aptitude or 0
        marks_per_aptitude = self.marks_per_aptitude or 1
        
        if self.technologies is None:
            tech_marks = 0
        else:
            tech_marks = len(self.technologies) * (self.num_technical_per_tech or 0) * (self.marks_per_technical or 1)
        
        return (num_aptitude * marks_per_aptitude) + tech_marks
    
    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        super().save(*args, **kwargs)