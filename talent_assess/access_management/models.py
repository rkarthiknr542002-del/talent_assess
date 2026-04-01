# access_management/models.py
from django.db import models
from django.utils import timezone
import secrets

class Participant(models.Model):
    """Students/Employees/Candidates"""
    # Remove organization field - comment it out
    # organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE)
    
    register_no = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Remove unique_together with organization
        # unique_together = ['organization', 'register_no']
        pass
    
    def __str__(self):
        return f"{self.name} ({self.register_no})"

class TestAccess(models.Model):
    """Link between Test and Participant with Token"""
    test = models.CharField(max_length=100)  # Store test ID as string for MongoDB
    participant = models.CharField(max_length=100)
    token = models.CharField(max_length=255, unique=True, default=secrets.token_urlsafe)
    is_used = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'test_access'
        unique_together = ['test', 'participant']
    
    def __str__(self):
        return f"Test: {self.test} - Participant: {self.participant}"