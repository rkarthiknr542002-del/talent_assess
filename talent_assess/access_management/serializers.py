# from rest_framework import serializers
# from .models import Participant, TestAccess

# class ParticipantSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Participant
#         fields = ['id', 'register_no', 'name', 'email', 'mobile', 'department', 'created_at']

# class TestAccessSerializer(serializers.ModelSerializer):
#     participant_name = serializers.CharField(source='participant.name', read_only=True)
#     participant_email = serializers.CharField(source='participant.email', read_only=True)
#     test_title = serializers.CharField(source='test.title', read_only=True)
    
#     class Meta:
#         model = TestAccess
#         fields = ['id', 'test', 'test_title', 'participant', 'participant_name', 
#                   'participant_email', 'token', 'is_used', 'attempted_at', 'created_at']

# access_management/serializers.py
from rest_framework import serializers
from .models import Participant, TestAccess

class ParticipantSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    
    class Meta:
        model = Participant
        fields = ['id', 'register_no', 'name', 'email', 'mobile', 'department', 'created_at']
        extra_kwargs = {
            'register_no': {
                'validators': []  # Remove unique validator to avoid Djongo recursion
            }
        }
    
    def get_id(self, obj):
        """Convert ObjectId to string"""
        return str(obj.id) if obj.id else None
    
    def validate_register_no(self, value):
        """Manual unique validation to avoid Djongo recursion"""
        if self.instance:
            # For update, check if register_no changed and already exists
            if self.instance.register_no != value:
                if Participant.objects.filter(register_no=value).exists():
                    raise serializers.ValidationError("Participant with this Register No already exists.")
        else:
            # For create, check if exists
            if Participant.objects.filter(register_no=value).exists():
                raise serializers.ValidationError("Participant with this Register No already exists.")
        return value

class TestAccessSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    participant_name = serializers.CharField(source='participant.name', read_only=True)
    participant_email = serializers.CharField(source='participant.email', read_only=True)
    test_title = serializers.CharField(source='test.title', read_only=True)
    
    class Meta:
        model = TestAccess
        fields = ['id', 'test', 'test_title', 'participant', 'participant_name', 
                  'participant_email', 'token', 'is_used', 'attempted_at', 'created_at']
    
    def get_id(self, obj):
        """Convert ObjectId to string"""
        return str(obj.id) if obj.id else None