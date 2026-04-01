import random
import string
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=4):
    """Generate numeric OTP"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp):
    """Send OTP via email"""
    subject = 'Your OTP for Password Reset'
    message = f'Your OTP is: {otp}. This OTP is valid for 10 minutes.'
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = 'Welcome to Talent Assess!'
    message = f'Hi {user.name},\n\nWelcome to Talent Assess! Your account has been created successfully.'
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )