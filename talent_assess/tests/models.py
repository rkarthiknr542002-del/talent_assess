from django.db import models
from djongo import models as djongo_models
from accounts.models import User
from test_templates.models import TestTemplate
from questions.models import Question
import uuid
from datetime import datetime
from django.utils import timezone

class Test(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]
    
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    test_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4, editable=False)
    
    # Relations
    candidate = djongo_models.ForeignKey(User, on_delete=models.CASCADE, related_name='tests', db_column='candidate', db_index=False)
    template = djongo_models.ForeignKey(TestTemplate, on_delete=models.SET_NULL, null=True, db_column='template')
    
    # Test snapshot
    experience_level = models.CharField(max_length=20)
    selected_technologies = models.JSONField(null=True, blank=True)  
    
    # Questions snapshot
    aptitude_questions = models.JSONField(default=list)  
    technical_questions = models.JSONField(default=dict)  
    
    # Answers
    answers = models.JSONField(default=dict) 
    
    # Status and timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Results
    total_marks = models.IntegerField(default=0)
    obtained_marks = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tests'
        indexes = [
            models.Index(fields=['test_id']),
            models.Index(fields=['candidate']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate percentage before saving
        if self.total_marks and self.total_marks > 0:
            self.percentage = (self.obtained_marks / self.total_marks) * 100
            self.percentage = round(self.percentage, 2)
            
            # Auto-set pass/fail based on percentage
            self.passed = self.percentage >= 70  # Adjust threshold as needed
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.test_id} - {self.candidate.email}"
    
    def start(self):
        """Start the test"""
        self.status = 'in_progress'
        self.start_time = timezone.now()  
        self.save()
    
    def submit(self):
        """Submit the test"""
        self.status = 'completed'
        self.end_time = timezone.now()  
        self.save()
    
    def expire(self):
        """Mark test as expired"""
        self.status = 'expired'
        self.end_time = datetime.now()
        self.save()
    
    def complete(self, answers=None):
        """Complete the test"""
        if self.status != 'in_progress':
            return False
        
        self.status = 'completed'
        self.end_time = timezone.now()
        
        if answers is not None:
            self.answers = answers
            self.calculate_results()
        
        self.save()
        return True
    
    def is_expired(self):
        """Check if test has expired based on duration"""
        if not self.start_time or self.status != 'in_progress':
            return False
        
        elapsed = (timezone.now() - self.start_time).total_seconds() / 60
        return elapsed > self.duration_minutes
    
    def get_remaining_seconds(self):
        """Get remaining time in seconds"""
        if not self.start_time:
            return self.duration_minutes * 60
        
        elapsed = (timezone.now() - self.start_time).total_seconds()
        remaining = (self.duration_minutes * 60) - elapsed
        return max(0, int(remaining))
    
    def get_all_questions(self):
        """Get all questions as a flat list"""
        questions = []
        if self.aptitude_questions:
            questions.extend(self.aptitude_questions)
        if self.technical_questions:
            for tech, tech_questions in self.technical_questions.items():
                for q in tech_questions:
                    q['technology'] = tech
                    questions.append(q)
        return questions
    
    def calculate_results(self):
        """Calculate and update test results"""
        questions = self.get_all_questions()
        
        total_marks = 0
        obtained_marks = 0
        
        for q in questions:
            q_id = str(q.get('_id', q.get('id', '')))
            selected = self.answers.get(q_id)
            correct = q.get('correct_answer')
            marks = q.get('marks', 1)
            
            total_marks += marks
            
            if selected is not None and selected == correct:
                obtained_marks += marks
        
        self.total_marks = total_marks
        self.obtained_marks = obtained_marks
        
        if total_marks > 0:
            self.percentage = (obtained_marks / total_marks) * 100
            self.percentage = round(self.percentage, 2)
            self.passed = self.percentage >= 70
        
        self.save()