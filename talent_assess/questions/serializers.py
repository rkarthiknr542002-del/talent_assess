from rest_framework import serializers
from .models import Question
from accounts.serializers import UserProfileSerializer

class QuestionSerializer(serializers.ModelSerializer):
    created_by_details = UserProfileSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            '_id', 'level', 'category', 'technology', 'question_text',
            'options', 'correct_answer', 'marks', 'explanation',
            'created_by_details', 'created_at', 'updated_at',
            'is_active', 'times_used', 'correct_count', 'wrong_count',
            'question_type', 'time_to_solve_seconds', 'language'
        ]
        read_only_fields = ['_id', 'created_at', 'updated_at', 'times_used', 'correct_count', 'wrong_count']
        extra_kwargs = {
            'correct_answer': {'write_only': True} 
        }
    
    def validate_options(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Options must be a list")
        if len(value) != 4:
            raise serializers.ValidationError("Exactly 4 options are required")
        return value
    
    def validate_correct_answer(self, value):
        if value < 0 or value > 3:
            raise serializers.ValidationError("Correct answer must be between 0 and 3")
        return value
    
    def validate(self, data):
        if data.get('category') == 'aptitude' and data.get('technology'):
            raise serializers.ValidationError({
                "technology": "Technology should not be set for aptitude questions"
            })
        
        if data.get('category') == 'technical' and not data.get('technology'):
            raise serializers.ValidationError({
                "technology": "Technology is required for technical questions"
            })
        
        return data

class QuestionBulkUploadSerializer(serializers.Serializer):
    questions = QuestionSerializer(many=True)
    
    def create(self, validated_data):
        questions = []
        for question_data in validated_data['questions']:
            question_data['created_by'] = self.context['request'].user
            questions.append(Question.objects.create(**question_data))
        return questions

class QuestionStatsSerializer(serializers.ModelSerializer):
    accuracy = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = ['_id', 'question_text', 'times_used', 'correct_count', 'wrong_count', 'accuracy']
    
    def get_accuracy(self, obj):
        if obj.times_used == 0:
            return 0
        return round((obj.correct_count / obj.times_used) * 100, 2)