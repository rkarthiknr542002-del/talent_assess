from rest_framework import serializers
from .models import Analytics

class AnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analytics
        fields = [
            '_id', 'date', 'total_tests_taken', 'total_candidates',
            'pass_count', 'fail_count', 'level_wise_stats',
            'technology_wise_stats', 'created_at', 'updated_at'
        ]
        read_only_fields = ['_id', 'created_at', 'updated_at']

class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    
    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("start_date must be before end_date")
        return data