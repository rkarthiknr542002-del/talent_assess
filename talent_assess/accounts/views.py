from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
import jwt
import secrets
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework import status
from bson import ObjectId
from bson.errors import InvalidId
from django.core.paginator import Paginator
from .models import User
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from core.exceptions import ValidationError, NotFoundError, UnauthorizedError
from core.permissions import IsAdmin, IsCandidate, IsOwnerOrAdmin

# Helper functions
def generate_reset_token(user):
    payload = {
        'user_id': str(user._id),
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'type': 'password_reset'
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def verify_reset_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if payload.get('type') != 'password_reset':
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def signup(request):
    """User Registration"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """User Login"""
    serializer = UserLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    try:
        user = User.objects.get(email=email)
        
        if not user.check_password(password):
            return Response({
                'success': False,
                'error': {
                    'code': 401,
                    'message': 'Invalid credentials'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'success': False,
                'error': {
                    'code': 401,
                    'message': 'Account is deactivated'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user.last_login = datetime.now()
        user.save()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = RefreshToken()
        
        refresh['user_id'] = str(user._id)
        refresh['email'] = user.email
        refresh['name'] = user.name
        refresh['role'] = user.role
        
        refresh['token_type'] = 'refresh'
        
        access_token = refresh.access_token
        access_token['user_id'] = str(user._id)
        access_token['email'] = user.email
        access_token['role'] = user.role
        access_token['token_type'] = 'access'
        
        print(f"Login successful for user: {user.email}")
        print(f"User _id: {user._id}")
        print(f"User _id type: {type(user._id)}")
        print(f"Token user_id: {str(user._id)}")
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': {
                    'id': str(user._id),
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                },
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh)
                }
            }
        })
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 401,
                'message': 'Invalid credentials'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout(request):
    """User Logout - Blacklist refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def change_password(request):
    """Change Password"""
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

def generate_reset_token(user):
    """
    Generate a password reset token
    """
    token = secrets.token_urlsafe(32)
    
    user.password_reset_token = token
    user.password_reset_token_created = timezone.now()
    user.save()
    
    return token

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    """Forgot Password - Send reset email"""
    serializer = ForgotPasswordSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        user = serializer.get_user()
        
        if not user:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        from .serializers import generate_reset_token_alt
        token = generate_reset_token_alt(user)
        
        try:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        except:
            frontend_url = 'http://localhost:5173'
        
        reset_url = f"{frontend_url}/reset-password?token={token}"
        
        try:
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_url}\n\n'
                f'This link will expire in 24 hours.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            print(f"Password reset email sent to {email}")
        except Exception as e:
            print(f"Email error: {e}")
            if settings.DEBUG:
                return Response({
                    'success': True,
                    'message': 'Password reset email sent if email exists',
                    'debug_token': token,
                    'debug_url': reset_url
                })
        
        return Response({
            'success': True,
            'message': 'Password reset email sent if email exists'
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """Reset password using token"""
    serializer = ResetPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        cache_key = serializer.validated_data.get('cache_key')
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        if cache_key:
            cache.delete(cache_key)
        
        return Response({
            'success': True,
            'message': 'Password reset successful'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'error': {
            'code': 400,
            'message': 'Invalid input',
            'details': serializer.errors
        }
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token(request):
    """Refresh Access Token"""
    return TokenRefreshView.as_view()(request)

@api_view(['POST'])
def verify_token(request):
    """Verify Token"""
    return Response({
        'success': True,
        'message': 'Token is valid'
    })

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        
        # Only admins can see all users
        if user.role == 'admin':
            queryset = User.objects.all()
        else:
            queryset = User.objects.filter(_id=user._id)
        
        # Apply filters from query parameters
        name = self.request.query_params.get('name')
        email = self.request.query_params.get('email')
        date_of_birth = self.request.query_params.get('date_of_birth')
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if date_of_birth:
            queryset = queryset.filter(date_of_birth=date_of_birth)
        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def search(self, request):
        """
        Search users with filters (admin only)
        GET /api/auth/users/search/?name=john&email=test&role=candidate
        """
        # Get search parameters
        name = request.query_params.get('name')
        email = request.query_params.get('email')
        date_of_birth = request.query_params.get('date_of_birth')
        role = request.query_params.get('role')
        is_active = request.query_params.get('is_active')
        
        # Start with all users
        queryset = User.objects.all()
        
        # Apply filters
        if name:
            queryset = queryset.filter(name__icontains=name)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if date_of_birth:
            queryset = queryset.filter(date_of_birth=date_of_birth)
        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Order by creation date
        queryset = queryset.order_by('-created_at')
        
        # Pagination
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', 10)
        
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        
        serializer = self.get_serializer(current_page, many=True)
        
        return Response({
            'success': True,
            'data': {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': int(page),
                'page_size': int(page_size),
                'has_next': current_page.has_next(),
                'has_previous': current_page.has_previous(),
                'results': serializer.data
            }
        })
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def candidates(self, request):
        """Get all candidates (Admin only) - Newest first"""
        # IMPORTANT: Add order_by('-created_at') here
        candidates = User.objects.filter(role='candidate').order_by('-created_at')
        serializer = self.get_serializer(candidates, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post', 'delete'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """Deactivate a user with debug info"""
        print("="*50)
        print(f"Deactivate called with pk: {pk}")
        print(f"pk type: {type(pk)}")
        
        all_users = User.objects.all()
        print(f"Total users in DB: {all_users.count()}")
        
        for user in all_users:
            print(f"DB User ID: {user._id}, Type: {type(user._id)}")
            print(f"  - Email: {user.email}")
            print(f"  - String compare: {str(user._id) == pk}")
        
        try:
            try:
                user = User.objects.get(_id=ObjectId(pk))
                print("Found using ObjectId")
            except:
                user = User.objects.get(_id=pk)
                print("Found using string")
                
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': f'User with ID {pk} not found'
            }, status=404)
        
        user.is_active = False
        user.save()
        
        return Response({
            'success': True,
            'message': f'User {user.email} deactivated'
        })
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAdmin])
    def permanent_delete(self, request, pk=None):
        """
        Hard delete - Permanently remove user from database
        DELETE /api/users/{id}/permanent-delete/
        """
        try:
            user = User.objects.get(_id=ObjectId(pk))
        except (InvalidId, User.DoesNotExist):
            return Response({
                'success': False,
                'message': f'User with ID {pk} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        email = user.email
        
        user.delete()
        
        return Response({
            'success': True,
            'message': f'User {email} permanently deleted'
        }, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_detail_by_email(request, email):
    """
    GET: Get user details by email
    """
    try:
        # Get user by email
        user = get_object_or_404(User, email=email)
        
        # Check permissions
        if request.user.role != 'admin' and request.user._id != user._id:
            return Response({
                'success': False,
                'message': 'You do not have permission to view this user'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = UserProfileSerializer(user)
        
        # Try to import TestResult with better error handling
        try:
            from test.models import TestResult
            print("✓ Successfully imported TestResult from test.models")
            
            # Get test history for this user
            test_results = TestResult.objects.filter(user=user).order_by('-created_at')
            test_count = test_results.count()
            passed_tests = test_results.filter(passed=True).count()
            
            # Get recent tests
            recent_tests = test_results[:5]
            recent_tests_data = [{
                'id': str(t._id),
                'template_name': t.template.name if t.template else 'Unknown',
                'score': t.score,
                'passed': t.passed,
                'created_at': t.created_at
            } for t in recent_tests]
            
            return Response({
                'success': True,
                'data': {
                    **serializer.data,
                    'test_history': {
                        'total_tests': test_count,
                        'passed_tests': passed_tests,
                        'failed_tests': test_count - passed_tests,
                        'pass_rate': round((passed_tests / test_count * 100), 2) if test_count > 0 else 0,
                        'recent_tests': recent_tests_data
                    }
                }
            })
            
        except ImportError as import_error:
            print(f"✗ ImportError: {import_error}")
            
            # Try alternative app names
            alternative_apps = ['tests', 'quiz', 'exam', 'assessment', 'candidate', 'testing']
            
            for app_name in alternative_apps:
                try:
                    module_path = f'{app_name}.models'
                    print(f"Trying to import from {module_path}...")
                    module = __import__(module_path, fromlist=['TestResult'])
                    TestResult = getattr(module, 'TestResult', None)
                    
                    if TestResult:
                        print(f"✓ Successfully imported TestResult from {app_name}.models")
                        
                        # Get test history
                        test_results = TestResult.objects.filter(user=user).order_by('-created_at')
                        test_count = test_results.count()
                        passed_tests = test_results.filter(passed=True).count()
                        
                        recent_tests = test_results[:5]
                        recent_tests_data = [{
                            'id': str(t._id),
                            'template_name': t.template.name if t.template else 'Unknown',
                            'score': t.score,
                            'passed': t.passed,
                            'created_at': t.created_at
                        } for t in recent_tests]
                        
                        return Response({
                            'success': True,
                            'data': {
                                **serializer.data,
                                'test_history': {
                                    'total_tests': test_count,
                                    'passed_tests': passed_tests,
                                    'failed_tests': test_count - passed_tests,
                                    'pass_rate': round((passed_tests / test_count * 100), 2) if test_count > 0 else 0,
                                    'recent_tests': recent_tests_data
                                }
                            }
                        })
                        
                except ImportError:
                    continue
                except Exception as e:
                    print(f"Error with {app_name}: {e}")
                    continue
            
            # If we get here, no TestResult model found
            print("⚠ No TestResult model found in any app")
            return Response({
                'success': True,
                'data': {
                    **serializer.data,
                    'test_history': None,
                    'message': 'Test history not available'
                }
            })
            
        except Exception as model_error:
            print(f"✗ Other error with TestResult: {model_error}")
            return Response({
                'success': True,
                'data': {
                    **serializer.data,
                    'test_history': None,
                    'error': str(model_error)
                }
            })
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_action_by_email(request, email):
    """
    POST: Perform actions on user by email (deactivate, activate, get_tests, etc.)
    """
    # Debug logging
    print(f"Received POST request for email: {email}")
    print(f"Request data: {request.data}")
    print(f"Request user: {request.user.email if request.user else 'None'}")
    
    # Check if user is admin
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Admin permission required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Get user by email
        user = get_object_or_404(User, email=email)
        
        # Get action from request data
        action = request.data.get('action')
        
        if not action:
            return Response({
                'success': False,
                'message': 'Action parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Action received: '{action}'")
        
        # Handle different actions
        if action == 'deactivate':
            user.is_active = False
            user.save()
            return Response({
                'success': True,
                'message': f'User {email} deactivated successfully'
            })
            
        elif action == 'activate':
            user.is_active = True
            user.save()
            return Response({
                'success': True,
                'message': f'User {email} activated successfully'
            })
            
        elif action == 'get_tests':
            # Try to import TestResult from various possible locations
            TestResult = None
            possible_apps = ['test', 'tests', 'quiz', 'exam', 'assessment']
            
            for app_name in possible_apps:
                try:
                    module = __import__(f'{app_name}.models', fromlist=['TestResult'])
                    TestResult = getattr(module, 'TestResult', None)
                    if TestResult:
                        print(f"Found TestResult in {app_name}.models")
                        break
                except ImportError:
                    continue
            
            if not TestResult:
                return Response({
                    'success': False,
                    'message': 'Test history not available'
                })
            
            # Get pagination parameters
            page = int(request.data.get('page', 1))
            page_size = int(request.data.get('page_size', 10))
            
            # Get test results
            test_results = TestResult.objects.filter(user=user).order_by('-created_at')
            total = test_results.count()
            
            # Paginate
            start = (page - 1) * page_size
            end = start + page_size
            paginated_results = test_results[start:end]
            
            results_data = [{
                'id': str(t._id),
                'template_name': t.template.name if t.template else 'Unknown',
                'template_technology': t.template.technologies if t.template else [],
                'score': t.score,
                'passed': t.passed,
                'started_at': t.started_at,
                'completed_at': t.completed_at,
                'created_at': t.created_at
            } for t in paginated_results]
            
            return Response({
                'success': True,
                'data': {
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size if total > 0 else 1,
                    'current_page': page,
                    'page_size': page_size,
                    'results': results_data
                }
            })
        
        # If action doesn't match any of the above
        return Response({
            'success': False,
            'message': f'Invalid action: "{action}". Allowed actions: deactivate, activate, get_tests'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': f'User with email {email} not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        print(f"Error in user_action_by_email: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)