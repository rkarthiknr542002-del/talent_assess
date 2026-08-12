

from rest_framework import serializers
from .models import TestTemplate, User
from accounts.serializers import UserProfileSerializer
import json
import logging
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'experience_level', 
                 'years_of_experience', 'technologies', 'phone_number',
                 'date_of_birth', 'gender', 'profile_photo', 'address',
                 'education', 'skills', 'resume_url', 'created_at', 'is_active']
        
class TestTemplateSerializer(serializers.ModelSerializer):
    created_by_details = UserProfileSerializer(source='created_by', read_only=True)
    total_questions = serializers.IntegerField(read_only=True)
    candidates = serializers.SerializerMethodField()
    candidate_count = serializers.SerializerMethodField()  # Add this for debugging
    candidate_by_email = serializers.SerializerMethodField()

    class Meta:
        model = TestTemplate
        fields = [
            '_id', 'name', 'description', 'experience_level', 'technologies',
            'num_aptitude', 'num_technical_per_tech', 'duration_minutes',
            'pass_percentage', 'created_by_details', 'created_at',
            'is_active', 'total_questions', 'candidates', 'candidate_count' ,'candidate_by_email'  # Add candidate_count
        ]
        read_only_fields = ['_id', 'created_at', 'total_questions']
    
    def get_candidates(self, obj):
        """
        Get candidates who match this test template's technologies
        """
        try:
            # Get all users with role='candidate'
            all_users = list(User.objects.all())
            candidates = [user for user in all_users if user.role == 'candidate' and user.is_active]
            
            print(f"Total candidates in DB: {len(candidates)}")  # Debug print
            
            if not candidates:
                print("No candidates found in database!")
                return []
            
            # Get template technologies
            template_techs = obj.technologies
            print(f"Template technologies: {template_techs}")  # Debug print
            
            if isinstance(template_techs, str):
                try:
                    template_techs = json.loads(template_techs)
                except:
                    template_techs = [template_techs]
            elif isinstance(template_techs, list):
                template_techs = [str(t).lower() if t else '' for t in template_techs]
            else:
                template_techs = []
            
            template_techs = [t for t in template_techs if t]  # Remove empty strings
            print(f"Processed template techs: {template_techs}")  # Debug print
            
            # Filter candidates
            matching_candidates = []
            for candidate in candidates:
                print(f"\nChecking candidate: {candidate.email}")  # Debug print
                print(f"Candidate technologies: {candidate.technologies}")  # Debug print
                
                if not candidate.technologies:
                    print("Candidate has no technologies")
                    continue
                
                # Process candidate technologies
                candidate_techs = candidate.technologies
                if isinstance(candidate_techs, str):
                    try:
                        candidate_techs = json.loads(candidate_techs)
                    except:
                        candidate_techs = [candidate_techs]
                elif isinstance(candidate_techs, list):
                    candidate_techs = [str(t).lower() if t else '' for t in candidate_techs]
                else:
                    candidate_techs = []
                
                candidate_techs = [t for t in candidate_techs if t]  # Remove empty strings
                print(f"Processed candidate techs: {candidate_techs}")  # Debug print
                
                # Check if any technology matches
                match_found = any(tech in candidate_techs for tech in template_techs)
                print(f"Match found: {match_found}")  # Debug print
                
                if match_found:
                    # Check experience level (optional)
                    if obj.experience_level and candidate.experience_level:
                        if candidate.experience_level.lower() == obj.experience_level.lower():
                            matching_candidates.append(candidate)
                            print(f"Added candidate with experience match")
                        else:
                            print(f"Experience mismatch: template={obj.experience_level}, candidate={candidate.experience_level}")
                    else:
                        matching_candidates.append(candidate)
                        print(f"Added candidate without experience check")
            
            print(f"\nTotal matching candidates: {len(matching_candidates)}")  # Debug print
            
            # Serialize
            serializer = UserSerializer(matching_candidates, many=True)
            return serializer.data
            
        except Exception as e:
            print(f"Error in get_candidates: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_candidate_count(self, obj):
        """Debug method to show total candidates in DB"""
        try:
            total_candidates = User.objects.filter(role='candidate', is_active=True).count()
            return total_candidates
        except:
            return 0
        
    def get_candidate_by_email(self, obj):
        """
        Get candidate details by email if provided in request
        """
        request = self.context.get('request')
        email = self.context.get('email') or (request.query_params.get('email') if request else None)
        
        if not email:
            return None
        
        try:
            candidate = User.objects.get(email=email, role='candidate', is_active=True)
            serializer = UserSerializer(candidate)
            return serializer.data
        except User.DoesNotExist:
            return {'error': f'Candidate not found with email: {email}'}
        except Exception as e:
            return {'error': str(e)}
        
    def validate_num_aptitude(self, value):
        """Prevent multiple aptitude values"""
        # Check if it's a list (multiple values)
        if isinstance(value, list):
            raise serializers.ValidationError(
                "Multiple aptitude values are not allowed. Please provide a single numeric value."
            )
        
        # Check if it's a string with commas (multiple values)
        if isinstance(value, str) and ',' in value:
            raise serializers.ValidationError(
                "Multiple aptitude values are not allowed. Please provide a single number."
            )
        
        # Ensure it's a valid number
        try:
            num_value = int(value)
            if num_value < 0:
                raise serializers.ValidationError("Number of aptitude questions cannot be negative")
            return num_value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Please provide a valid number for aptitude questions")
    
    def validate_num_technical_per_tech(self, value):
        """Prevent multiple technical values"""
        # Check if it's a list (multiple values)
        if isinstance(value, list):
            raise serializers.ValidationError(
                "Multiple technical values are not allowed. Please provide a single numeric value."
            )
        
        # Check if it's a string with commas (multiple values)
        if isinstance(value, str) and ',' in value:
            raise serializers.ValidationError(
                "Multiple technical values are not allowed. Please provide a single number."
            )
        
        # Ensure it's a valid number
        try:
            num_value = int(value)
            if num_value < 0:
                raise serializers.ValidationError("Number of technical questions cannot be negative")
            return num_value
        except (ValueError, TypeError):
            raise serializers.ValidationError("Please provide a valid number for technical questions")
    
    # Optional: If you want to validate the entire object together
    
    def validate(self, data):
        """Validate using direct PyMongo query with auto-detection"""
        
        from django.conf import settings
        from pymongo import MongoClient
        
        num_aptitude = data.get('num_aptitude')
        num_technical_per_tech = data.get('num_technical_per_tech')
        technologies = data.get('technologies')
        
        try:
            client = MongoClient(
                settings.DATABASES['default']['CLIENT']['host'],
                settings.DATABASES['default']['CLIENT']['port']
            )
            db = client[settings.DATABASES['default']['NAME']]
            
            # Try to find the correct collection
            collection_name = None
            possible_names = ['questions', 'Question', 'question', 'quiz_question']
            
            for name in possible_names:
                if name in db.list_collection_names():
                    collection_name = name
                    break
            
            if not collection_name:
                print("No questions collection found!")
                return data
            
            questions_collection = db[collection_name]
            
            # Get a sample document to understand structure
            sample = questions_collection.find_one()
            if sample:
                print(f"Sample document fields: {list(sample.keys())}")
                
                # Detect field names
                type_field = 'question_type' if 'question_type' in sample else 'type' if 'type' in sample else None
                active_field = 'is_active' if 'is_active' in sample else 'active' if 'active' in sample else None
                
                if not type_field or not active_field:
                    print("Could not detect field names, skipping validation")
                    return data
                
                # 1. Validate aptitude questions count
                if num_aptitude:
                    experience_level = data.get('experience_level')
                    level_map = {
                        'intern': ['intern', 'junior', 'fresher'],
                        'junior': ['junior'],
                        'mid': ['mid', 'intermediate'],
                        'senior': ['senior']
                    }
                    levels_to_check = level_map.get(
                        experience_level.lower() if experience_level else '',
                        [experience_level]
                    )

                        
                    available_aptitude = questions_collection.count_documents({
                        'category': 'aptitude',
                        'level': experience_level.lower(),
                        'is_active': True
                    })
                    
                    print(f"Aptitude Available: {available_aptitude}, Requested: {num_aptitude}")
                    
                    if num_aptitude > available_aptitude:
                        raise serializers.ValidationError({
                            'num_aptitude': (
                                f'Only {available_aptitude} aptitude questions available '
                                f'for {experience_level} level. You requested {num_aptitude}.'
                        )
                        })
                
                # 2. Validate technical questions count
                if num_technical_per_tech and technologies:
                    tech_list = []
                    if isinstance(technologies, str):
                        try:
                            tech_list = json.loads(technologies)
                        except:
                            tech_list = [technologies]
                    elif isinstance(technologies, list):
                        tech_list = technologies
                    
                    for tech in tech_list:
                        available_technical = questions_collection.count_documents({
                            'category': 'technical',
                            'technology': {'$regex': f'^{tech}$', '$options': 'i'},
                            'level': experience_level.lower(),
                            'is_active': True
                        })
                        
                        print(f"Technical for {tech} - Available: {available_technical}, Requested: {num_technical_per_tech}")
                        
                        if num_technical_per_tech > available_technical:
                            raise serializers.ValidationError({
                                'num_technical_per_tech': f'Only {available_technical} technical questions available for "{tech}". You requested {num_technical_per_tech}.'
                            })
            
            client.close()
        except ValidationError:
            raise   # 🔥 MUST
        except Exception as e:
            print(f"Validation error: {e}")
            raise 
        
        
        return data