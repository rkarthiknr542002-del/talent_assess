from rest_framework import serializers
from .models import QuestionBank
from questions.models import Question
from questions.serializers import QuestionSerializer
from accounts.serializers import UserProfileSerializer

class QuestionBankSerializer(serializers.ModelSerializer):
    created_by_details = UserProfileSerializer(source='created_by', read_only=True)
    total_questions = serializers.IntegerField(read_only=True)
    total_marks = serializers.IntegerField(read_only=True)
    question_details = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionBank
        fields = [
            '_id', 'name', 'description', 'level', 'technologies',
            'questions', 'question_details', 'created_by_details',
            'created_at', 'is_active', 'category', 'total_questions', 'total_marks'
        ]
        read_only_fields = ['_id', 'created_at', 'total_questions', 'total_marks']
    
    def get_question_details(self, obj):
        questions = []
        for q_id in obj.questions[:10]: 
            try:
                question = Question.objects.get(_id=q_id)
                questions.append({
                    '_id': str(question._id),
                    'text': question.question_text[:100],
                    'marks': question.marks
                })
            except Question.DoesNotExist:
                continue
        return questions
    
    def validate_questions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Questions must be a list")
        
        invalid_ids = []
        for q_id in value:
            try:
                Question.objects.get(_id=q_id)
            except Question.DoesNotExist:
                invalid_ids.append(str(q_id))
        
        if invalid_ids:
            raise serializers.ValidationError(f"Invalid question IDs: {invalid_ids}")
        
        return value