# access_management/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import pandas as pd
from datetime import datetime, timedelta 
import secrets
from django.db import IntegrityError

# Import from your apps
from tests.models import Test
from results.models import Result
from .models import Participant, TestAccess


# ==================== HELPER FUNCTIONS ====================

def safe_get_test(test_identifier):
    """Safely get test by various identifiers without using Django ORM filters"""
    try:
        # Try to find test using MongoDB's _id directly
        # This bypasses Djongo's SQL translation
        from django.db import connection
        
        # For MongoDB, we need to use raw query or direct collection access
        # Since we're using Djongo, we'll try different approaches
        
        # Approach 1: Try to get by _id using MongoDB ObjectId
        try:
            return Test.objects.get(_id=test_identifier)
        except:
            pass
        
        # Approach 2: Try by test_id field
        try:
            # Use filter with first() instead of get() to avoid multiple results
            tests = list(Test.objects.filter(test_id=test_identifier)[:1])
            if tests:
                return tests[0]
        except:
            pass
        
        # Approach 3: Try by id field
        try:
            tests = list(Test.objects.filter(id=test_identifier)[:1])
            if tests:
                return tests[0]
        except:
            pass
        
        # Approach 4: Try by pk
        try:
            return Test.objects.get(pk=test_identifier)
        except:
            pass
        
        raise Test.DoesNotExist
    except Exception as e:
        raise Test.DoesNotExist(f"Test not found: {str(e)}")


def safe_get_all_participants():
    """Safely get all participants without using .exists()"""
    try:
        # Use list() to evaluate the queryset immediately
        participants = list(Participant.objects.all())
        return participants
    except Exception as e:
        # If error occurs, return empty list
        print(f"Error getting participants: {str(e)}")
        return []
    
# ==================== PARTICIPANT VIEWS ====================

class ParticipantListView(APIView):
    """List all participants"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        participants = Participant.objects.all()
        data = []
        for p in participants:
            data.append({
                'id': str(p.id),
                'register_no': p.register_no,
                'name': p.name,
                'email': p.email,
                'mobile': p.mobile,
                'department': p.department,
                'created_at': p.created_at
            })
        return Response(data)


class ParticipantCreateView(APIView):
    """Create a new participant"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        register_no = request.data.get('register_no')
        name = request.data.get('name')
        email = request.data.get('email')
        mobile = request.data.get('mobile', '')
        department = request.data.get('department', '')
        
        # Try to create directly with exception handling
        try:
            participant = Participant.objects.create(
                register_no=register_no,
                name=name,
                email=email,
                mobile=mobile,
                department=department
            )
            
            return Response({
                'id': str(participant.id),
                'register_no': participant.register_no,
                'name': participant.name,
                'email': participant.email,
                'mobile': participant.mobile,
                'department': participant.department,
                'created_at': participant.created_at
            }, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            return Response({
                'error': f'Participant with register_no {register_no} already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Check if it's a duplicate error
            error_msg = str(e)
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                return Response({
                    'error': f'Participant with register_no {register_no} already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)


class ParticipantDetailView(APIView):
    """Get, update, delete a participant"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return Participant.objects.get(id=pk)
        except Participant.DoesNotExist:
            return None
        except Exception:
            # For MongoDB ObjectId issues
            try:
                return Participant.objects.get(pk=pk)
            except:
                return None
    
    def get(self, request, pk):
        participant = self.get_object(pk)
        if not participant:
            return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'id': str(participant.id),
            'register_no': participant.register_no,
            'name': participant.name,
            'email': participant.email,
            'mobile': participant.mobile,
            'department': participant.department,
            'created_at': participant.created_at
        })
    
    def put(self, request, pk):
        participant = self.get_object(pk)
        if not participant:
            return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Update fields
            participant.name = request.data.get('name', participant.name)
            participant.email = request.data.get('email', participant.email)
            participant.mobile = request.data.get('mobile', participant.mobile)
            participant.department = request.data.get('department', participant.department)
            
            new_register_no = request.data.get('register_no')
            if new_register_no and new_register_no != participant.register_no:
                participant.register_no = new_register_no
            
            participant.save()
            return Response({
                'id': str(participant.id),
                'register_no': participant.register_no,
                'name': participant.name,
                'email': participant.email,
                'mobile': participant.mobile,
                'department': participant.department,
                'created_at': participant.created_at
            })
        except IntegrityError:
            return Response({
                'error': f'Participant with register_no {new_register_no} already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        participant = self.get_object(pk)
        if not participant:
            return Response({'error': 'Participant not found'}, status=status.HTTP_404_NOT_FOUND)
        participant.delete()
        return Response({'message': 'Participant deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class ParticipantBulkUploadView(APIView):
    """Upload participants from Excel file"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            df = pd.read_excel(file)
            participants = []
            errors = []
            
            required_columns = ['register_no', 'name', 'email']
            for col in required_columns:
                if col not in df.columns:
                    return Response({
                        'error': f'Missing required column: {col}. Required: register_no, name, email'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            for index, row in df.iterrows():
                register_no = str(row['register_no'])
                
                try:
                    participant = Participant.objects.create(
                        register_no=register_no,
                        name=row['name'],
                        email=row['email'],
                        mobile=row.get('mobile', ''),
                        department=row.get('department', '')
                    )
                    participants.append({
                        'id': str(participant.id),
                        'register_no': participant.register_no,
                        'name': participant.name,
                        'email': participant.email,
                        'mobile': participant.mobile,
                        'department': participant.department
                    })
                except IntegrityError:
                    errors.append(f"Row {index+2}: {register_no} already exists")
                except Exception as e:
                    errors.append(f"Row {index+2}: {str(e)}")
            
            return Response({
                'message': f'Successfully uploaded {len(participants)} participants',
                'count': len(participants),
                'participants': participants,
                'errors': errors if errors else None
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ==================== TEST ACCESS VIEWS ====================

class TestAccessListView(APIView):
    """List all test access records"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        test_access = TestAccess.objects.all()
        data = []
        for access in test_access:
            data.append({
                'id': str(access.id),
                'test': access.test,
                'participant': str(access.participant.id),
                'participant_name': access.participant.name,
                'participant_email': access.participant.email,
                'token': access.token,
                'is_used': access.is_used,
                'attempted_at': access.attempted_at,
                'created_at': access.created_at
            })
        return Response(data)


# access_management/views.py - Update TestAccessCreateView

class TestAccessCreateView(APIView):
    """Create a new test access"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            participant_id = request.data.get('participant')
            test_id = request.data.get('test')
            
            if not participant_id or not test_id:
                return Response({
                    'error': 'Both participant and test are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert participant_id to string for proper matching
            participant_id_str = str(participant_id)
            
            # Try to get participant by exact ID
            try:
                # First try with id field
                participant = Participant.objects.get(id=participant_id_str)
            except Participant.DoesNotExist:
                try:
                    # Try with pk
                    participant = Participant.objects.get(pk=participant_id_str)
                except Participant.DoesNotExist:
                    return Response({
                        'error': f'Participant with id {participant_id} not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'error': f'Error finding participant: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if test access already exists
            try:
                existing = TestAccess.objects.filter(
                    test=str(test_id), 
                    participant=participant
                ).first()
                
                if existing:
                    return Response({
                        'error': 'Test access already exists for this participant',
                        'existing': {
                            'id': str(existing.id),
                            'token': existing.token,
                            'is_used': existing.is_used
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
            except:
                pass
            
            # Create new test access
            test_access = TestAccess.objects.create(
                test=str(test_id),
                participant=participant,
                token=secrets.token_urlsafe(32)
            )
            
            return Response({
                'id': str(test_access.id),
                'test': test_access.test,
                'participant': str(test_access.participant.id),
                'participant_name': test_access.participant.name,
                'participant_register_no': test_access.participant.register_no,
                'token': test_access.token,
                'is_used': test_access.is_used,
                'created_at': test_access.created_at
            }, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            return Response({
                'error': 'Test access already exists for this participant'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class TestAccessDetailView(APIView):
    """Get, update, delete a test access"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return TestAccess.objects.get(id=pk)
        except TestAccess.DoesNotExist:
            return None
        except:
            try:
                return TestAccess.objects.get(pk=pk)
            except:
                return None
    
    def get(self, request, pk):
        access = self.get_object(pk)
        if not access:
            return Response({'error': 'Test access not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'id': str(access.id),
            'test': access.test,
            'participant': str(access.participant.id),
            'participant_name': access.participant.name,
            'token': access.token,
            'is_used': access.is_used,
            'attempted_at': access.attempted_at
        })
    
    def delete(self, request, pk):
        access = self.get_object(pk)
        if not access:
            return Response({'error': 'Test access not found'}, status=status.HTTP_404_NOT_FOUND)
        access.delete()
        return Response({'message': 'Test access deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


# access_management/views.py - Update TestAccessGenerateLinksView

# import secrets
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.db import IntegrityError
# from django.db.models import Count

# class TestAccessGenerateLinksView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         test_identifier = request.data.get('test_id')
        
#         if not test_identifier:
#             return Response({'error': 'test_id is required'}, status=400)
        
#         base_url = request.build_absolute_uri('/')[:-1]
        
#         try:
#             test = safe_get_test(test_identifier)
#         except Test.DoesNotExist as e:
#             return Response({'error': str(e)}, status=404)
        
#         test_title = getattr(test, 'title', f"Test_{str(test_identifier)[:8]}")
        
#         from access_management.models import Participant
        
#         participants = list(Participant.objects.all())
        
#         if not participants:
#             return Response({'error': 'No participants found'}, status=400)
        
#         # ✅ delete old
#         TestAccess.objects.filter(test=test).delete()
        
#         new_links = []
#         errors = []
        
#         for participant in participants:
#             try:
#                 # ✅ FIX 1: ensure participant is saved
#                 if not participant.pk:
#                     participant.save()
                
#                 token = secrets.token_urlsafe(32)
                
#                 access = TestAccess.objects.create(
#                     test=test,
#                     participant=participant,
#                     token=token
#                 )
                
#                 link = f"{base_url}/signup?token={token}"
                
#                 new_links.append({
#                     'participant_id': str(participant.pk),
#                     'name': participant.name,
#                     'register_no': participant.register_no,
#                     'token': token,
#                     'link': link
#                 })
                
#                 print(f"✅ Created link for {participant.name}")
            
#             except Exception as e:
#                 print(f"❌ Error for {participant.name}: {str(e)}")
#                 errors.append({
#                     'name': participant.name,
#                     'error': str(e)
#                 })
        
#         return Response({
#             'success': True,
#             'message': f'Generated {len(new_links)} links for {test_title}',
#             'test_id': str(test._id) if hasattr(test, '_id') else str(test.id),
#             'test_title': test_title,
#             'total_participants': len(participants),
#             'links_generated': len(new_links),
#             'base_url': base_url,
#             'links': new_links,
#             'errors': errors if errors else None
#         }, status=201 if new_links else 200)



# views.py
import jwt
import secrets
from datetime import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import TestAccess, Participant
import logging

logger = logging.getLogger(__name__)

def safe_get_test(test_identifier):
    """Get test safely using either _id or test_id"""
    from tests.models import Test
    
    try:
        # Try to find by _id (MongoDB ObjectId)
        test = Test.objects.filter(_id=test_identifier).first()
        if test:
            return test
        
        # Try by test_id field
        test = Test.objects.filter(test_id=test_identifier).first()
        if test:
            return test
        
        raise Exception("Test not found")
        
    except Exception as e:
        raise Exception(f"Test not found: {str(e)}")

# views.py - Modified version
# class TestAccessGenerateLinksView(APIView):
#     """Admin மட்டும் test links generate பண்ணும்"""
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         try:
#             user = request.user
            
#             # Admin check
#             if not user.is_staff and not user.is_superuser:
#                 return Response({
#                     'error': 'Only admin can generate test links'
#                 }, status=status.HTTP_403_FORBIDDEN)
            
#             # Get test_id from request
#             test_identifier = request.data.get('test_id')
#             if not test_identifier:
#                 return Response({
#                     'error': 'test_id is required'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Get test using safe_get_test function
#             try:
#                 test = safe_get_test(test_identifier)
#             except Exception as e:
#                 return Response({
#                     'error': 'Test not found',
#                     'detail': str(e),
#                     'test_id': test_identifier
#                 }, status=status.HTTP_404_NOT_FOUND)
            
#             # Get test ID properly (MongoDB uses _id)
#             test_stored_id = str(test._id) if hasattr(test, '_id') else str(test.id)
            
#             # Get test title
#             test_title = getattr(test, 'title', None)
#             if not test_title:
#                 if hasattr(test, 'template') and test.template:
#                     test_title = str(test.template)
#                 else:
#                     test_title = f"Test_{test_identifier[:8]}"
            
#             # Base URL
#             base_url = request.data.get('base_url', 'http://localhost:8000')
            
#             # Get participants - Get actual Participant objects
#             try:
#                 participants = list(Participant.objects.all())
#                 print(f"Found {len(participants)} participants")
                
#                 # Remove duplicates by register_no
#                 unique_participants = {}
#                 for p in participants:
#                     if p.register_no not in unique_participants:
#                         unique_participants[p.register_no] = p
#                 participants = list(unique_participants.values())
#                 print(f"After removing duplicates: {len(participants)} participants")
                
#             except Exception as e:
#                 print(f"Error fetching participants: {e}")
#                 return Response({
#                     'error': 'Error fetching participants',
#                     'detail': str(e)
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#             if not participants:
#                 return Response({
#                     'error': 'No participants found',
#                     'solution': 'Please add participants first'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             # Delete old links
#             try:
#                 deleted_count = TestAccess.objects.filter(test=test_stored_id).delete()
#                 print(f"Deleted {deleted_count[0]} existing links")
#             except Exception as e:
#                 print(f"Error deleting links: {e}")
            
#             # Generate new links
#             generated_links = []
#             failed_participants = []
            
#             for participant in participants:
#                 try:
#                     # IMPORTANT: Use the participant OBJECT, not just register_no string
#                     participant_object = participant  # This is the Participant object
#                     participant_register = participant.register_no
                    
#                     # Create token payload
#                     payload = {
#                         "admin_id": str(user.id),
#                         "test_id": test_stored_id,
#                         "participant_id": participant_register,
#                         "type": "test_access",
#                         "iat": datetime.utcnow()
#                     }
                    
#                     token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                    
#                     # Save test access - PASS THE PARTICIPANT OBJECT, NOT STRING
#                     TestAccess.objects.create(
#                         test=test_stored_id,
#                         participant=participant_object,  # Pass the object, not string
#                         token=token,
#                         is_used=False
#                     )
                    
#                     # Create link
#                     invite_link = f"{base_url}/signup?token={token}"
                    
#                     generated_links.append({
#                         # 'participant_id': participant_register,
#                         # 'name': participant.name,
#                         # 'register_no': participant.register_no,
#                         'token': token,
#                         'link': invite_link
#                     })
#                     print(f"✅ Created link for {participant.name}")
                    
#                 except Exception as e:
#                     print(f"❌ Error for {participant.name}: {str(e)}")
#                     failed_participants.append({
#                         'name': participant.name,
#                         'register_no': participant.register_no,
#                         'error': str(e)
#                     })
#                     continue
            
#             return Response({
#                 'success': True,
#                 'message': f'Generated {len(generated_links)} new links for test: {test_title}',
#                 'test_id': test_stored_id,
#                 'test_title': test_title,
#                 'total_participants': len(participants),
#                 'links_generated': len(generated_links),
#                 'failed_count': len(failed_participants),
#                 'links': generated_links,
#                 'failed_participants': failed_participants if failed_participants else None,
#                 'base_url': base_url
#             }, status=status.HTTP_201_CREATED if generated_links else status.HTTP_200_OK)
            
#         except Exception as e:
#             logger.exception(f"Generate test links failed: {str(e)}")
#             return Response({
#                 'error': 'Failed to generate test links',
#                 'detail': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestAccessGenerateLinksView(APIView):
    """Admin மட்டும் test links generate பண்ணும்"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            user = request.user
            
            # Admin check
            if not user.is_staff and not user.is_superuser:
                return Response({
                    'error': 'Only admin can generate test links'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get test_template_id from request
            test_template_id = request.data.get('test_template_id')
            if not test_template_id:
                return Response({
                    'error': 'test_template_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"🔍 Looking for test template with ID: {test_template_id}")
            
            # Try to get test template
            try:
                from tests.models import TestTemplate
                
                test_template = None
                
                # Try different ways to find the test template
                try:
                    test_template = TestTemplate.objects.get(id=test_template_id)
                except:
                    pass
                
                if not test_template:
                    try:
                        test_template = TestTemplate.objects.get(_id=test_template_id)
                    except:
                        pass
                
                if not test_template:
                    try:
                        from bson import ObjectId
                        obj_id = ObjectId(test_template_id)
                        test_template = TestTemplate.objects.get(_id=obj_id)
                    except:
                        pass
                
                if not test_template:
                    return Response({
                        'error': 'Test template not found',
                        'detail': f'No test template found with ID: {test_template_id}',
                        'test_template_id': test_template_id
                    }, status=status.HTTP_404_NOT_FOUND)
                
            except Exception as e:
                print(f"❌ Error fetching test template: {str(e)}")
                return Response({
                    'error': 'Test template not found',
                    'detail': str(e),
                    'test_template_id': test_template_id
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get test template ID properly
            test_template_stored_id = str(test_template._id) if hasattr(test_template, '_id') else str(test_template.id)
            
            # Get test template title
            test_title = getattr(test_template, 'name', None)
            if not test_title:
                test_title = f"Test_{test_template_id[:8]}"
            
            print(f"📝 Test template: {test_title} (ID: {test_template_stored_id})")
            
            # Base URL
            base_url = request.data.get('base_url', 'http://localhost:8000')
            
            # Generate a single link without participants
            # Create token payload
            payload = {
                "admin_id": str(user.id),
                "test_template_id": test_template_stored_id,
                "type": "test_access",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(days=7)
            }
            
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Create link
            invite_link = f"{base_url}/signup?token={token}"
            
            generated_links = [{
                'token': token,
                'link': invite_link,
                # 'test_template_id': test_template_stored_id,
                # 'test_template_title': test_title
            }]
            
            return Response({
                'success': True,
                'message': f'Generated link for test template',
                'test_template_id': test_template_stored_id,
                # 'test_template_title': test_title,
                'links_generated': 1,
                'links': generated_links,
                'base_url': base_url
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Generate test links failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Failed to generate test links',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class AdminTestLinksView(APIView):
    """Admin-க்கான test links management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, test_id=None):  # IMPORTANT: Add test_id parameter
        try:
            user = request.user
            
            # Admin check
            if not user.is_staff and not user.is_superuser:
                return Response({
                    'error': 'Only admin can view test links'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get test_id from URL path if provided, else from query params
            if test_id:
                # Using path parameter
                print(f"Test ID from URL: {test_id}")
            else:
                # Using query parameter
                test_id = request.query_params.get('test_id')
                print(f"Test ID from query: {test_id}")
            
            if not test_id:
                return Response({
                    'error': 'test_id is required',
                    'usage': 'GET /api/access/admin/test-links/<test_id>/ or ?test_id=xxx'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get all test access records for this test
            test_access_records = TestAccess.objects.filter(test=test_id)
            
            # Convert to list to avoid Djongo issues
            records = list(test_access_records)
            
            if not records:
                return Response({
                    'success': True,
                    'message': 'No links found for this test',
                    'test_id': test_id,
                    'total_links': 0,
                    'links': []
                })
            
            # Prepare response data
            links_data = []
            for record in records:
                # Get participant details
                participant_name = "Unknown"
                participant_register = record.participant
                
                try:
                    # Try to get participant object
                    if hasattr(record, 'participant') and record.participant:
                        if isinstance(record.participant, Participant):
                            participant_name = record.participant.name
                            participant_register = record.participant.register_no
                        else:
                            # If participant is stored as string (register_no)
                            participant = Participant.objects.filter(register_no=record.participant).first()
                            if participant:
                                participant_name = participant.name
                                participant_register = participant.register_no
                except Exception as e:
                    print(f"Error getting participant: {e}")
                
                # Generate link
                base_url = request.build_absolute_uri('/').rstrip('/')
                link = f"{base_url}/signup?token={record.token}"
                
                links_data.append({
                    'id': str(record.id) if hasattr(record, 'id') else None,
                    'participant_id': participant_register,
                    'participant_name': participant_name,
                    'token': record.token,
                    'link': link,
                    'is_used': record.is_used,
                    'attempted_at': record.attempted_at,
                    'created_at': record.created_at
                })
            
            # Count statistics
            total_links = len(links_data)
            used_links = len([l for l in links_data if l['is_used']])
            unused_links = total_links - used_links
            
            return Response({
                'success': True,
                'test_id': test_id,
                'total_links': total_links,
                'used_links': used_links,
                'unused_links': unused_links,
                'links': links_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Get test links failed: {str(e)}")
            return Response({
                'error': 'Failed to fetch test links',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """Delete all links for a test"""
        try:
            # Admin check
            if not request.user.is_staff and not request.user.is_superuser:
                return Response({
                    'error': 'Only admin can delete test links'
                }, status=status.HTTP_403_FORBIDDEN)
            
            test_id = request.data.get('test_id')
            if not test_id:
                return Response({
                    'error': 'test_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete all test access records
            deleted_count = TestAccess.objects.filter(test=test_id).delete()
            
            return Response({
                'success': True,
                'message': f'Deleted {deleted_count[0]} links for test {test_id}',
                'deleted_count': deleted_count[0]
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class TakeTestView(APIView):
#     """Test link-ஐ click பண்ணினால் test-க்கு போகும் வியூ"""
#     permission_classes = []  # Public access
    
#     def get(self, request):
#         token = request.GET.get('token')
        
#         if not token:
#             return Response({
#                 'error': 'Token is required'
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             # Decode token
#             payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            
#             # Check token type
#             if payload.get('type') != 'test_access':
#                 return Response({
#                     'error': 'Invalid token type'
#                 }, status=status.HTTP_400_BAD_REQUEST)
            
#             test_id = payload.get('test_id')
#             participant_id = payload.get('participant_id')
#             vendor_id = payload.get('vendor_id')
            
#             # Get test details
#             test = Test.objects.get(id=test_id)
            
#             # Get participant details
#             participant = Participant.objects.get(id=participant_id)
            
#             # Mark token as used
#             test_access = TestAccess.objects.filter(
#                 test=test,
#                 participant=participant,
#                 token=token
#             ).first()
            
#             if test_access and not test_access.is_used:
#                 test_access.is_used = True
#                 test_access.attempted_at = datetime.now()
#                 test_access.save()
            
#             # Return test page HTML
#             html_content = f"""
#             <!DOCTYPE html>
#             <html>
#             <head>
#                 <title>{test.title}</title>
#                 <style>
#                     body {{
#                         font-family: Arial, sans-serif;
#                         margin: 0;
#                         padding: 20px;
#                         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#                     }}
#                     .container {{
#                         max-width: 800px;
#                         margin: 0 auto;
#                         background: white;
#                         border-radius: 10px;
#                         padding: 30px;
#                         box-shadow: 0 10px 40px rgba(0,0,0,0.1);
#                     }}
#                     .header {{
#                         text-align: center;
#                         border-bottom: 2px solid #667eea;
#                         padding-bottom: 20px;
#                         margin-bottom: 30px;
#                     }}
#                     .participant-info {{
#                         background: #f8f9fa;
#                         padding: 15px;
#                         border-radius: 8px;
#                         margin-bottom: 20px;
#                     }}
#                     .btn-start {{
#                         background: #667eea;
#                         color: white;
#                         padding: 12px 30px;
#                         border: none;
#                         border-radius: 5px;
#                         font-size: 16px;
#                         cursor: pointer;
#                         width: 100%;
#                     }}
#                     .btn-start:hover {{
#                         background: #5a67d8;
#                     }}
#                 </style>
#             </head>
#             <body>
#                 <div class="container">
#                     <div class="header">
#                         <h1>📝 {test.title}</h1>
#                         <p>Welcome to your assessment</p>
#                     </div>
                    
#                     <div class="participant-info">
#                         <h3>👤 Participant Details</h3>
#                         <p><strong>Name:</strong> {participant.name}</p>
#                         <p><strong>Register No:</strong> {participant.register_no}</p>
#                         <p><strong>Email:</strong> {participant.email}</p>
#                     </div>
                    
#                     <div class="test-info">
#                         <h3>📋 Test Information</h3>
#                         <p><strong>Duration:</strong> {getattr(test, 'duration', 60)} minutes</p>
#                         <p><strong>Total Questions:</strong> {test.questions.count() if hasattr(test, 'questions') else 0}</p>
#                         <p><strong>Instructions:</strong> Read each question carefully before answering.</p>
#                     </div>
                    
#                     <button class="btn-start" onclick="startTest()">
#                         🚀 Start Test Now
#                     </button>
#                 </div>
                
#                 <script>
#                     const testId = '{test_id}';
#                     const participantId = '{participant_id}';
#                     const token = '{token}';
                    
#                     function startTest() {{
#                         window.location.href = `/test/{test_id}/take/?token=${{token}}&participant=${{participantId}}`;
#                     }}
#                 </script>
#             </body>
#             </html>
#             """
            
#             return Response(html_content, content_type='text/html')
            
#         except jwt.ExpiredSignatureError:
#             return Response({
#                 'error': 'Link has expired. Please request a new link.'
#             }, status=status.HTTP_401_UNAUTHORIZED)
#         except jwt.InvalidTokenError:
#             return Response({
#                 'error': 'Invalid token. Please check your link.'
#             }, status=status.HTTP_401_UNAUTHORIZED)
#         except Exception as e:
#             return Response({
#                 'error': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# access_management/views.py - Update download_links

class TestAccessDownloadLinksView(APIView):
    """Download all test links as Excel"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        test_id = request.query_params.get('test_id')
        
        if not test_id:
            return Response({'error': 'test_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Try to get test by _id
            try:
                test = Test.objects.get(_id=test_id)
            except:
                try:
                    test = Test.objects.get(id=test_id)
                except:
                    test = Test.objects.get(pk=test_id)
        except Test.DoesNotExist:
            return Response({'error': 'Test not found'}, status=status.HTTP_404_NOT_FOUND)
        
        test_id_str = str(test._id if hasattr(test, '_id') else test.id)
        accesses = TestAccess.objects.filter(test=test_id_str)
        
        if not accesses.exists():
            return Response({'error': 'No links generated for this test yet'}, status=status.HTTP_404_NOT_FOUND)
        
        data = []
        base_url = request.build_absolute_uri('/').rstrip('/')
        
        for access in accesses:
            data.append({
                'Name': access.participant.name,
                'Register No': access.participant.register_no,
                'Email': access.participant.email,
                'Department': access.participant.department,
                'Test Link': f"{base_url}/api/access/tests/take/{access.token}/",
                'Status': 'Completed' if access.is_used else 'Pending',
                'Attempted At': access.attempted_at if access.attempted_at else 'Not attempted'
            })
        
        df = pd.DataFrame(data)
        response = Response(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="test_links_{test.title}.xlsx"'
        df.to_excel(response, index=False)
        return response


# ==================== TAKE TEST VIEWS (Public - No Auth) ====================

# access_management/views.py - Update TakeTestAPIView

class TakeTestAPIView(APIView):
    """Public API for students to take test using token"""
    
    def get(self, request, token):
        """Get test details using token"""
        try:
            access = TestAccess.objects.get(token=token)
        except TestAccess.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)
        
        if access.is_used:
            return Response({
                'error': 'You have already completed this test',
                'status': 'already_attempted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get test from tests app using _id for MongoDB
        try:
            # Try different ways to get test
            try:
                test = Test.objects.get(_id=access.test)
            except:
                try:
                    test = Test.objects.get(id=access.test)
                except:
                    test = Test.objects.get(pk=access.test)
        except Test.DoesNotExist:
            return Response({'error': 'Test not found'}, status=status.HTTP_404_NOT_FOUND)
        
        now = timezone.now()
        
        # Check test availability
        if hasattr(test, 'start_time') and test.start_time:
            if now < test.start_time:
                return Response({
                    'error': 'Test has not started yet',
                    'start_time': test.start_time
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if hasattr(test, 'end_time') and test.end_time:
            if now > test.end_time:
                return Response({
                    'error': 'Test has expired',
                    'end_time': test.end_time
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get questions
        questions = test.questions.all()
        
        questions_list = []
        for q in questions:
            questions_list.append({
                'id': str(q._id if hasattr(q, '_id') else q.id),
                'question_text': q.question_text,
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d
            })
        
        return Response({
            'test_id': str(test._id if hasattr(test, '_id') else test.id),
            'title': test.title,
            'description': getattr(test, 'description', ''),
            'duration': test.duration_minutes if hasattr(test, 'duration_minutes') else 60,
            'total_questions': len(questions_list),
            'questions': questions_list,
            'token': token,
            'participant_name': access.participant.name,
            'participant_email': access.participant.email,
            'participant_register_no': access.participant.register_no
        })
    
    def post(self, request, token):
        """Submit test answers and calculate result"""
        try:
            access = TestAccess.objects.get(token=token)
        except TestAccess.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)
        
        if access.is_used:
            return Response({
                'error': 'You have already completed this test',
                'status': 'already_attempted'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get test from tests app
        try:
            try:
                test = Test.objects.get(_id=access.test)
            except:
                try:
                    test = Test.objects.get(id=access.test)
                except:
                    test = Test.objects.get(pk=access.test)
        except Test.DoesNotExist:
            return Response({'error': 'Test not found'}, status=status.HTTP_404_NOT_FOUND)
        
        answers = request.data.get('answers', {})
        
        # Calculate marks
        questions = test.questions.all()
        total_marks = 0
        obtained_marks = 0
        
        for question in questions:
            total_marks += question.marks if hasattr(question, 'marks') else 1
            selected = answers.get(str(question._id if hasattr(question, '_id') else question.id))
            if selected and selected.lower() == question.correct_option.lower():
                obtained_marks += question.marks if hasattr(question, 'marks') else 1
        
        percentage = (obtained_marks / total_marks) * 100 if total_marks > 0 else 0
        
        # Save result
        result = Result.objects.create(
            test=test,
            participant_name=access.participant.name,
            participant_email=access.participant.email,
            participant_register_no=access.participant.register_no,
            obtained_marks=obtained_marks,
            total_marks=total_marks,
            percentage=round(percentage, 2)
        )
        
        # Mark token as used
        access.is_used = True
        access.attempted_at = timezone.now()
        access.ip_address = request.META.get('REMOTE_ADDR')
        access.save()
        
        return Response({
            'message': 'Test submitted successfully',
            'result_id': str(result.id),
            'obtained_marks': obtained_marks,
            'total_marks': total_marks,
            'percentage': round(percentage, 2),
            'passed': percentage >= 40
        })