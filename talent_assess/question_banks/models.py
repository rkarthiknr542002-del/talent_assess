from django.db import models
from djongo import models as djongo_models
from accounts.models import User
from questions.models import Question
from datetime import datetime

class QuestionBank(models.Model):
    LEVEL_CHOICES = [
        ('intern', 'Intern'),
        ('junior', 'Junior'),
        ('mid', 'Mid'),
        ('senior', 'Senior'),
    ]
    
    CATEGORY_CHOICES = [
        ('aptitude', 'Aptitude'),
        ('technical', 'Technical'),
        ('mixed', 'Mixed'),
    ]
    
    _id = djongo_models.ObjectIdField(primary_key=True, db_column='_id')
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    technologies = models.JSONField(null=True, blank=True)  # ['python', 'django']
    questions = models.JSONField(default=list)  # Array of question ObjectIds
    created_by = djongo_models.ForeignKey(User, on_delete=models.CASCADE, db_column='created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    
    class Meta:
        db_table = 'question_banks'
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def total_questions(self):
        return len(self.questions)
    
    @property
    def total_marks(self):
        total = 0
        for q_id in self.questions:
            try:
                question = Question.objects.get(_id=q_id)
                total += question.marks
            except Question.DoesNotExist:
                continue
        return total
    
    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        super().save(*args, **kwargs)