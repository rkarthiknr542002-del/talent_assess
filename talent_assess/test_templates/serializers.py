# # from rest_framework import serializers
# # from .models import TestTemplate, User
# # from accounts.serializers import UserProfileSerializer
# # from django.db.models import Q

# # class UserSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = User
# #         fields = ['id', 'email', 'name', 'role', 'experience_level', 
# #                  'years_of_experience', 'technologies', 'phone_number',
# #                  'date_of_birth', 'gender', 'profile_photo', 'address',
# #                  'education', 'skills', 'resume_url', 'created_at', 'is_active']
        
# # class TestTemplateSerializer(serializers.ModelSerializer):
# #     created_by_details = UserProfileSerializer(source='created_by', read_only=True)
# #     total_questions = serializers.IntegerField(read_only=True)
# #     candidates = serializers.SerializerMethodField()

# #     class Meta:
# #         model = TestTemplate
# #         fields = [
# #             '_id', 'name', 'description', 'experience_level', 'technologies',
# #             'num_aptitude', 'num_technical_per_tech', 'duration_minutes',
# #             'pass_percentage', 'created_by_details', 'created_at',
# #             'is_active', 'total_questions','candidates'
# #         ]
# #         read_only_fields = ['_id', 'created_at', 'total_questions']
    
# #     def validate_technologies(self, value):
# #         if not isinstance(value, list):
# #             raise serializers.ValidationError("Technologies must be a list")
# #         if len(value) == 0:
# #             raise serializers.ValidationError("At least one technology is required")
# #         return value
    
# #     def validate(self, data):
        
# #         return data
    
# #     def get_candidates(self, obj):
# #         """
# #         Get all candidates who have taken or are assigned to this test
# #         """
# #         # Method 1: If you have a TestResult model linking users to tests
# #         from .models import TestResult  # Import here to avoid circular imports
        
# #         # Get unique candidates who have taken this test
# #         test_results = TestResult.objects.filter(test_template=obj).select_related('user')
# #         candidates = [result.user for result in test_results if result.user]
        
# #         # Remove duplicates (if a candidate took the test multiple times)
# #         unique_candidates = []
# #         seen_ids = set()
# #         for candidate in candidates:
# #             if candidate.id not in seen_ids:
# #                 seen_ids.add(candidate.id)
# #                 unique_candidates.append(candidate)
        
# #         # Serialize candidate details
# #         serializer = UserSerializer(unique_candidates, many=True)
# #         return serializer.data

# from rest_framework import serializers
# from .models import TestTemplate, User
# from accounts.serializers import UserProfileSerializer
# from django.db.models import Q
# import json

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'name', 'role', 'experience_level', 
#                  'years_of_experience', 'technologies', 'phone_number',
#                  'date_of_birth', 'gender', 'profile_photo', 'address',
#                  'education', 'skills', 'resume_url', 'created_at', 'is_active']
        
# class TestTemplateSerializer(serializers.ModelSerializer):
#     created_by_details = UserProfileSerializer(source='created_by', read_only=True)
#     total_questions = serializers.IntegerField(read_only=True)
#     candidates = serializers.SerializerMethodField()

#     class Meta:
#         model = TestTemplate
#         fields = [
#             '_id', 'name', 'description', 'experience_level', 'technologies',
#             'num_aptitude', 'num_technical_per_tech', 'duration_minutes',
#             'pass_percentage', 'created_by_details', 'created_at',
#             'is_active', 'total_questions', 'candidates'
#         ]
#         read_only_fields = ['_id', 'created_at', 'total_questions']
    
#     def validate_technologies(self, value):
#         if not isinstance(value, list):
#             raise serializers.ValidationError("Technologies must be a list")
#         if len(value) == 0:
#             raise serializers.ValidationError("At least one technology is required")
#         return value
    
#     def validate(self, data):
#         return data
    
#     def get_candidates(self, obj):
#         """
#         Get candidates who match this test template's technologies
#         Fixed for MongoDB/Djongo
#         """
#         try:
#             # Get all candidates - use list() to force evaluation with MongoDB
#             all_users = list(User.objects.all())
#             candidates = [user for user in all_users if user.role == 'candidate' and user.is_active]
            
#             # Get template technologies
#             template_techs = obj.technologies
#             if isinstance(template_techs, str):
#                 try:
#                     template_techs = json.loads(template_techs)
#                 except:
#                     template_techs = [template_techs]
#             elif isinstance(template_techs, list):
#                 template_techs = [t.lower() if isinstance(t, str) else t for t in template_techs]
#             else:
#                 template_techs = []
            
#             # Convert to list of strings
#             template_techs = [str(t).lower() for t in template_techs if t]
            
#             # Filter candidates whose technologies match
#             matching_candidates = []
#             for candidate in candidates:
#                 if not candidate.technologies:
#                     continue
                    
#                 candidate_techs = candidate.technologies
#                 if isinstance(candidate_techs, str):
#                     try:
#                         candidate_techs = json.loads(candidate_techs)
#                     except:
#                         candidate_techs = [candidate_techs]
#                 elif isinstance(candidate_techs, list):
#                     candidate_techs = [t.lower() if isinstance(t, str) else t for t in candidate_techs]
#                 else:
#                     candidate_techs = []
                
#                 # Convert to list of strings
#                 candidate_techs = [str(t).lower() for t in candidate_techs if t]
                
#                 # Check if any technology matches
#                 if any(tech in candidate_techs for tech in template_techs):
#                     # Also check experience level if needed (optional)
#                     if obj.experience_level and candidate.experience_level:
#                         if candidate.experience_level.lower() == obj.experience_level.lower():
#                             matching_candidates.append(candidate)
#                     else:
#                         matching_candidates.append(candidate)
            
#             # Limit to 10 for performance
#             matching_candidates = matching_candidates[:10]
            
#             # Serialize
#             serializer = UserSerializer(matching_candidates, many=True)
#             return serializer.data
            
#         except Exception as e:
#             print(f"Error in get_candidates: {str(e)}")
#             return []  # Return empty list on error

from rest_framework import serializers
from .models import TestTemplate, User
from accounts.serializers import UserProfileSerializer
import json
import logging

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