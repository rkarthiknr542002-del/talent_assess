import random
import string
import hashlib
import jwt
from django.conf import settings
from datetime import datetime, timedelta

def generate_random_string(length=10):
    """Generate random string"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_test_id():
    """Generate unique test ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = generate_random_string(6).upper()
    return f"TST-{timestamp}-{random_part}"

def hash_string(text):
    """Hash a string using SHA256"""
    return hashlib.sha256(text.encode()).hexdigest()

def create_password_reset_token(user):
    """Create password reset token"""
    payload = {
        'user_id': str(user._id),
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'type': 'password_reset'
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def verify_password_reset_token(token):
    """Verify password reset token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if payload.get('type') != 'password_reset':
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None