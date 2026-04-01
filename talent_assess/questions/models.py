from django.db import models
from djongo import models as djongo_models
from accounts.models import User
from datetime import datetime

class Category(models.Model):
    """Question category (Aptitude, Technical, etc.)"""
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    name = models.CharField(max_length=50, unique=True)  
    display_name = models.CharField(max_length=100)  
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.display_name

class Technology(models.Model):
    """Technology (Python, JavaScript, Java, etc.)"""
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    name = models.CharField(max_length=50, unique=True) 
    display_name = models.CharField(max_length=100)  
    description = models.TextField(blank=True, null=True)
    category = djongo_models.ForeignKey(Category, on_delete=models.CASCADE, related_name='technologies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'technologies'
        verbose_name_plural = 'Technologies'
    
    def __str__(self):
        return self.display_name
        
class Question(models.Model):
    LEVEL_CHOICES = [
        ('intern', 'Intern'),
        ('junior', 'Junior'),
        ('mid', 'Mid'),
        ('senior', 'Senior'),
    ]
    
    CATEGORY_CHOICES = [
        ('aptitude', 'Aptitude'),
        ('technical', 'Technical'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
    ]
    
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('tamil', 'Tamil'),
        ('hindi', 'Hindi'),
    ]
    
    # Basic Info
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES,  null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    technology = models.CharField(max_length=100, null=True, blank=True)  
    
    # Question Content
    question_text = models.TextField( null=True, blank=True)
    options = models.JSONField( null=True, blank=True)  
    correct_answer = models.IntegerField( null=True, blank=True)  
    marks = models.IntegerField(default=1)
    explanation = models.TextField(null=True, blank=True)
    
    # Metadata
    created_by = djongo_models.ForeignKey(User, on_delete=models.CASCADE, db_column='created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Statistics
    times_used = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    wrong_count = models.IntegerField(default=0)
    
    # Additional Fields
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    time_to_solve_seconds = models.IntegerField(default=60)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='english')
    
    class Meta:
        db_table = 'questions'
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['technology']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.question_text[:50]}"
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)
    
    def update_stats(self, is_correct):
        """Update question statistics"""
        self.times_used += 1
        if is_correct:
            self.correct_count += 1
        else:
            self.wrong_count += 1
        self.save()