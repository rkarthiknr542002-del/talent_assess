from rest_framework import serializers
from bson import ObjectId
from .models import Test
from test_templates.models import TestTemplate
from accounts.serializers import UserProfileSerializer
from test_templates.serializers import TestTemplateSerializer
from .utils import convert_objectid_to_str


class ObjectIdField(serializers.Field):
    """Custom field for MongoDB ObjectId"""
    
    def to_representation(self, value):
        if value is None:
            return None

        if isinstance(value, str):
            return value

        if hasattr(value, '__str__'):
            try:
                return str(value)
            except:
                return None
        
        return None
    
    def to_internal_value(self, data):
        if not data:
            return None
        try:
            return ObjectId(str(data))
        except:
            raise serializers.ValidationError('Invalid ObjectId format')


class TestSerializer(serializers.ModelSerializer):
    candidate_details = UserProfileSerializer(source='candidate', read_only=True)
    template_details = TestTemplateSerializer(source='template', read_only=True)
    remaining_seconds = serializers.SerializerMethodField()
    _id = ObjectIdField(read_only=True)
    candidate = ObjectIdField(read_only=True)
    template = ObjectIdField(read_only=True, allow_null=True)
    
    class Meta:
        model = Test
        fields = [
            '_id', 'test_id', 'candidate', 'candidate_details', 'template', 'template_details',
            'experience_level', 'selected_technologies', 'status', 'start_time', 'end_time',
            'duration_minutes', 'remaining_seconds', 'total_marks', 'obtained_marks',
            'percentage', 'passed', 'created_at'
        ]
        read_only_fields = ['_id', 'test_id', 'status', 'start_time', 'end_time',
                           'total_marks', 'obtained_marks', 'percentage', 'passed', 'created_at']
    
    def get_remaining_seconds(self, obj):
        return obj.get_remaining_seconds()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return convert_objectid_to_str(data)


class TestDetailSerializer(serializers.ModelSerializer):
    """Serializer for test details including questions"""
    aptitude_questions = serializers.SerializerMethodField()
    technical_questions = serializers.SerializerMethodField()
    remaining_seconds = serializers.SerializerMethodField()
    _id = ObjectIdField(read_only=True)
    
    class Meta:
        model = Test
        fields = [
            '_id', 'test_id', 'experience_level', 'selected_technologies',
            'aptitude_questions', 'technical_questions', 'status',
            'duration_minutes', 'remaining_seconds', 'start_time', 'end_time'
        ]
    
    def get_remaining_seconds(self, obj):
        return obj.get_remaining_seconds()
    
    def _extract_question_data(self, q):
        """Helper to extract question data regardless of key format"""
        if isinstance(q, dict):
            question_id = str(q.get('_id', q.get('id', '')))
            return {
                '_id': question_id,
                'text': q.get('text', q.get('question_text', '')),
                'options': q.get('options', []),
                'marks': q.get('marks', 1)
            }
        else:
            return {
                '_id': str(getattr(q, '_id', getattr(q, 'id', ''))),
                'text': getattr(q, 'question_text', getattr(q, 'text', '')),
                'options': getattr(q, 'options', []),
                'marks': getattr(q, 'marks', 1)
            }
    
    def get_aptitude_questions(self, obj):
        questions = []
        for q in obj.aptitude_questions:
            questions.append(self._extract_question_data(q))
        return questions
    
    def get_technical_questions(self, obj):
        result = {}
        for tech, questions in obj.technical_questions.items():
            result[tech] = []
            for q in questions:
                result[tech].append(self._extract_question_data(q))
        return result
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        if '_id' in data:
            data['id'] = data.pop('_id')
        
        for field in ['start_time', 'end_time', 'created_at', 'updated_at']:
            if data.get(field):
                if hasattr(data[field], 'isoformat'):
                    data[field] = data[field].isoformat()
        
        return data


class TestCreateSerializer(serializers.Serializer):
    template_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    experience_level = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    technologies = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        allow_empty=True,
        default=list
    )
    num_aptitude = serializers.IntegerField(required=False, default=5, min_value=0)
    num_technical = serializers.IntegerField(required=False, default=10, min_value=0)
    
    def validate_technologies(self, value):
        """Handle technologies that might come as string or list"""
        if value is None:
            return []
        if isinstance(value, str):
            if ',' in value:
                return [tech.strip() for tech in value.split(',') if tech.strip()]
            else:
                return [value]
        if isinstance(value, list):
            return value
        return []
    
    def validate(self, data):
        template_id = data.get('template_id')
        experience_level = data.get('experience_level')
        technologies = data.get('technologies', [])
        
        if template_id:
            try:
                template = TestTemplate.objects.get(_id=ObjectId(template_id))
                if not template.is_active:
                    raise serializers.ValidationError("Template is inactive")
                
                if not experience_level:
                    data['experience_level'] = template.experience_level
                
                if not technologies:
                    data['technologies'] = template.technologies or []
                
                if data.get('num_aptitude', 5) == 5:  
                    data['num_aptitude'] = getattr(template, 'num_aptitude', 5)
                
                if data.get('num_technical', 10) == 10:  
                    data['num_technical'] = getattr(template, 'num_technical_per_tech', 10)
                
            except TestTemplate.DoesNotExist:
                raise serializers.ValidationError(f"Template with ID {template_id} not found")
            except Exception as e:
                raise serializers.ValidationError(f"Error validating template: {str(e)}")
        
        if not data.get('experience_level'):
            raise serializers.ValidationError("experience_level is required")
        
        if not data.get('technologies'):
            raise serializers.ValidationError("At least one technology is required")
        
        return data


class TestSubmitSerializer(serializers.Serializer):
    answers = serializers.JSONField(required=False, default=dict)  
    
    def validate_answers(self, value):
        if value is None:
            return {}
        
        if not isinstance(value, dict):
            if isinstance(value, str):
                try:
                    import json
                    return json.loads(value)
                except:
                    raise serializers.ValidationError("Answers must be a valid JSON object")
            else:
                raise serializers.ValidationError("Answers must be a dictionary")
        
        return value
    
    def validate(self, data):
        if 'answers' not in data:
            data['answers'] = {}
        return data