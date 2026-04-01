from rest_framework import serializers
from .models import User
import re
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
import pymongo
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework import serializers
from django.core.cache import cache
import secrets
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from pymongo import MongoClient
from accounts.models import User

class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    years_of_experience = serializers.FloatField(required=False, allow_null=True)
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('intern', 'Intern'),
        ('junior', 'Junior'),
        ('mid', 'Mid'),
        ('senior', 'Senior'),
    ]
    experience_level = serializers.ChoiceField(
        required=False,
        allow_null=True,
        choices=EXPERIENCE_LEVEL_CHOICES,
        error_messages={
            'invalid_choice': 'Please select a valid experience level (beginner, intermediate, advanced, expert)',
            'null': 'Experience level cannot be null'
        }
    )
    
    technologies = serializers.JSONField(required=False,default=list, error_messages={'invalid': 'Technologies must be a valid JSON array'})
    
    phone_number = serializers.CharField(required=False,allow_null=True,allow_blank=True, max_length=20,error_messages={'max_length': 'Phone number cannot exceed 20 characters'})

    date_of_birth = serializers.DateField(required=False,allow_null=True,error_messages={'invalid': 'Please enter a valid date in YYYY-MM-DD format'})
    
    # Gender with choices - Define ONLY ONCE
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer Not to Say'),
    ]
    gender = serializers.ChoiceField(
        required=False,
        allow_null=True,
        choices=GENDER_CHOICES,
        error_messages={
            'invalid_choice': 'Please select a valid gender option'
        }
    )
    
    def validate_email(self, value):        
        try:
            client = MongoClient(settings.DATABASES['default']['CLIENT']['host'])
            db = client[settings.DATABASES['default']['NAME']]
            
            if db.users.find_one({'email': value}):
                raise serializers.ValidationError("User with this email already exists")
        except Exception:
            try:
                User.objects.get(email=value)
                raise serializers.ValidationError("User with this email already exists")
            except ObjectDoesNotExist:
                pass
        
        return value
    
    def validate_years_of_experience(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Years of experience cannot be negative")
        if value is not None and value > 50:
            raise serializers.ValidationError("Years of experience cannot be more than 50")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value:
            import re
            cleaned = re.sub(r'[\s\-\(\)]', '', value)
            
            if not re.match(r'^\+?\d{10,15}$', cleaned):
                raise serializers.ValidationError(
                    "Please enter a valid phone number with country code (e.g., +1234567890)"
                )
        return value
    
    def validate_date_of_birth(self, value):
        """Validate date of birth is not in future"""
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future")
        return value
    
    def validate_technologies(self, value):
        """Validate technologies is a list"""
        if value is not None and not isinstance(value, list):
            raise serializers.ValidationError("Technologies must be a list")
        
        if value:
            for tech in value:
                if not isinstance(tech, str):
                    raise serializers.ValidationError("Each technology must be a string")
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        
        data.pop('confirm_password')
        
        clean_data = {}
        for key, value in data.items():
            if value is not None:
                clean_data[key] = value
            elif key in ['technologies'] and value is None:
                clean_data[key] = []
        
        return clean_data
    
    def create(self, validated_data):
        from accounts.models import User
        return User.objects.create_user(**validated_data)
    
    def to_representation(self, instance):
        from .serializers import UserProfileSerializer
        return UserProfileSerializer(instance).data

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'role', 'experience_level',
            'years_of_experience', 'technologies', 'phone_number',
            'date_of_birth', 'gender', 'profile_photo', 'address',
            'education', 'skills', 'resume_url', 'created_at','is_active'
        ]
        read_only_fields = ['id', 'email', 'role', 'created_at']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match"})
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            self.context['user'] = user
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
    
    def get_user(self):
        """Helper method to get the validated user"""
        return self.context.get('user')

def generate_reset_token_alt(user):
    """
    Generate token and store in cache instead of model
    """
    token = secrets.token_urlsafe(32)
    
    user_id = str(user._id)  
    
    print(f"Storing token for user: {user.email}, user_id: {user_id}") 
    
    cache.set(f'password_reset_{token}', {
        'user_id': user_id,  
        'created': timezone.now().isoformat()
    }, timeout=60*60*24)  
    
    stored_data = cache.get(f'password_reset_{token}')
    print(f"Verified stored data: {stored_data}")  
    
    return token

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        
        token = data['token']
        print(f"Looking for token: {token}")  
        print(f"Cache key: password_reset_{token}") 
        
        token_data = cache.get(f'password_reset_{token}')
        
        print(f"Token data from cache: {token_data}") 
        
        if not token_data:
            raise serializers.ValidationError({
                'token': 'Invalid or expired token'
            })
        
        try:
            created = datetime.fromisoformat(token_data['created'])
            if timezone.now() > created + timedelta(hours=24):
                cache.delete(f'password_reset_{token}')
                raise serializers.ValidationError({
                    'token': 'Token has expired'
                })
        except (ValueError, KeyError) as e:
            print(f"Date parsing error: {e}") 
            raise serializers.ValidationError({
                'token': 'Invalid token data'
            })
        
        try:
            print(f"Looking for user with _id: {token_data['user_id']}")  
            print(f"User ID type: {type(token_data['user_id'])}")  
            
            from bson import ObjectId
            user = User.objects.get(_id=ObjectId(token_data['user_id']))
            
            data['user'] = user
            data['cache_key'] = f'password_reset_{token}'
            print(f"User found: {user.email}")  
            
        except Exception as e:
            print(f"Error finding user: {e}") 
            raise serializers.ValidationError({
                'token': 'User not found'
            })
        
        return data