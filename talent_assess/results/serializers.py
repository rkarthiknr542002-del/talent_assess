from rest_framework import serializers
from .models import Result
from accounts.serializers import UserProfileSerializer
from tests.serializers import TestSerializer

class ResultSerializer(serializers.ModelSerializer):
    candidate_details = UserProfileSerializer(source='candidate', read_only=True)
    test_details = TestSerializer(source='test', read_only=True)
    
    class Meta:
        model = Result
        fields = [
            '_id', 'test', 'test_details', 'candidate', 'candidate_details',
            'total_questions', 'attempted', 'correct', 'wrong', 'skipped',
            'total_marks', 'obtained_marks', 'percentage', 'passed',
            'category_wise', 'technology_wise', 'evaluated_at'
        ]
        read_only_fields = ['_id', 'evaluated_at']

class ResultDetailSerializer(serializers.ModelSerializer):
    """Detailed result with question results"""
    candidate_details = UserProfileSerializer(source='candidate', read_only=True)
    
    class Meta:
        model = Result
        fields = [
            '_id', 'test', 'candidate', 'candidate_details',
            'total_questions', 'attempted', 'correct', 'wrong', 'skipped',
            'total_marks', 'obtained_marks', 'percentage', 'passed',
            'category_wise', 'technology_wise', 'question_results', 'evaluated_at'
        ]