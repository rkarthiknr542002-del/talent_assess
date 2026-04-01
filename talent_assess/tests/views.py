# tests/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
import random
import traceback
from bson.errors import InvalidId
from bson import ObjectId
from .models import Test
from .serializers import TestSerializer, TestDetailSerializer, TestCreateSerializer, TestSubmitSerializer
from questions.models import Question
from test_templates.models import TestTemplate
from core.permissions import IsCandidate, IsOwnerOrAdmin
from core.exceptions import ValidationError
from .utils import safe_response, convert_objectid_to_str
import uuid

def create_test_logic(user, data):
    """Shared logic for creating a test - returns Response object"""
    
    print(f"Creating test with data: {data}")
    
    serializer = TestCreateSerializer(data=data)
    if serializer.is_valid():
        validated_data = serializer.validated_data
        print(f"Validated data: {validated_data}")
        
        template_id = validated_data.get('template_id')
        experience_level = validated_data.get('experience_level')
        technologies = validated_data.get('technologies', [])
        num_aptitude = validated_data.get('num_aptitude', 5)
        num_technical = validated_data.get('num_technical', 10)
        duration = 30
        
        template = None
        
        if template_id and str(template_id).strip():
            try:
                template = TestTemplate.objects.get(_id=ObjectId(template_id))
                duration = getattr(template, 'duration_minutes', 30)
                print(f"Using template: {template.name}")
            except:
                pass
        
        print(f"Final config - Level: {experience_level}, Technologies: {technologies}")
        
        print("\n=== CHECKING DATABASE ===")
        
        all_questions = Question.objects.all()
        print(f"Total questions in DB: {all_questions.count()}")
        
        aptitude_count = Question.objects.filter(category__iexact='aptitude').count()
        technical_count = Question.objects.filter(category__iexact='technical').count()
        print(f"Aptitude questions: {aptitude_count}")
        print(f"Technical questions: {technical_count}")
        
        level_count = Question.objects.filter(level=experience_level).count()
        print(f"Questions with level '{experience_level}': {level_count}")
        
        for tech in technologies:
            tech_count = Question.objects.filter(technology__iexact=tech).count()
            print(f"Questions with technology '{tech}' (case-insensitive): {tech_count}")
        
        for tech in technologies:
            combined = Question.objects.filter(
                category__iexact='technical',
                technology__iexact=tech,
                level=experience_level,
                is_active=True
            ).count()
            print(f"Active '{tech}' questions for level '{experience_level}': {combined}")
        
        print("=== END CHECK ===\n")
        
        aptitude_questions = []
        if num_aptitude > 0:
            try:
                aptitude_qs = list(Question.objects.filter(
                    category__iexact='aptitude',
                    level=experience_level,
                    is_active=True
                ))
                
                print(f"Found {len(aptitude_qs)} aptitude questions for level {experience_level}")
                
                if len(aptitude_qs) < num_aptitude:
                    return Response({
                        'success': False,
                        'message': f'Only {len(aptitude_qs)} aptitude questions available for {experience_level} level. Required: {num_aptitude}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                selected = random.sample(aptitude_qs, num_aptitude)
                for q in selected:
                    aptitude_questions.append({
                        '_id': str(q._id),
                        'text': q.question_text,
                        'options': q.options,
                        'correct_answer': q.correct_answer,
                        'marks': q.marks,
                        'explanation': q.explanation,
                        'category': 'aptitude'
                    })
            except Exception as e:
                print(f"Error fetching aptitude questions: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Error fetching aptitude questions: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        technical_questions = {}
        for tech in technologies:
            try:
                tech_qs = list(Question.objects.filter(
                    category__iexact='technical',
                    technology__iexact=tech,
                    level=experience_level,
                    is_active=True
                ))
                
                print(f"Found {len(tech_qs)} {tech} questions for level {experience_level}")
                
                if len(tech_qs) < num_technical:
                    return Response({
                        'success': False,
                        'message': f'Only {len(tech_qs)} {tech} questions available for {experience_level} level. Required: {num_technical}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                selected = random.sample(tech_qs, num_technical)
                technical_questions[tech] = []
                for q in selected:
                    technical_questions[tech].append({
                        '_id': str(q._id),
                        'text': q.question_text,
                        'options': q.options,
                        'correct_answer': q.correct_answer,
                        'marks': q.marks,
                        'explanation': q.explanation,
                        'category': 'technical',
                        'technology': tech
                    })
            except Exception as e:
                print(f"Error fetching {tech} questions: {str(e)}")
                return Response({
                    'success': False,
                    'message': f'Error fetching {tech} questions: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            test = Test.objects.create(
                candidate=user,
                template=template,
                experience_level=experience_level,
                selected_technologies=technologies,
                aptitude_questions=aptitude_questions,
                technical_questions=technical_questions,
                duration_minutes=duration,
                status='pending',
                answers={},
                total_marks=sum(q['marks'] for q in aptitude_questions) + 
                           sum(q['marks'] for tech_qs in technical_questions.values() for q in tech_qs),
                obtained_marks=0,
                percentage=0,
                passed=False
            )
            
            print(f"Test created successfully with ID: {test._id}")
            print(f"Aptitude questions: {len(aptitude_questions)}")
            print(f"Technical questions: {sum(len(q) for q in technical_questions.values())}")
            
        except Exception as e:
            print(f"Error creating test: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error creating test: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = TestSerializer(test)
        
        response_data = {
            'success': True,
            'message': 'Test created successfully',
            'data': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def test_list(request):
    """
    GET: List all tests (with filters and pagination)
    POST: Create new test
    """
    if request.method == 'GET':
        if request.user.role == 'admin':
            queryset = Test.objects.all()
        else:
            queryset = Test.objects.filter(candidate=request.user)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        level_filter = request.query_params.get('level')
        if level_filter:
            queryset = queryset.filter(experience_level=level_filter)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(test_id__icontains=search) |
                Q(candidate__name__icontains=search)
            )
        
        from_date = request.query_params.get('from_date')
        if from_date:
            queryset = queryset.filter(started_at__gte=from_date)
        
        to_date = request.query_params.get('to_date')
        if to_date:
            queryset = queryset.filter(started_at__lte=to_date)
        
        queryset = queryset.order_by('-created_at')
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        
        serializer = TestSerializer(current_page, many=True)
        
        response_data = {
            'success': True,
            'data': {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': current_page.has_next(),
                'has_previous': current_page.has_previous(),
                'results': serializer.data
            }
        }
        
        return safe_response(response_data)
    
    elif request.method == 'POST':
        return create_test_logic(request.user, request.data)


@api_view(['POST'])
@permission_classes([IsCandidate])
def start_test(request):
    """Start a new test (candidate endpoint)"""
    return create_test_logic(request.user, request.data)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrAdmin])
def test_detail(request, pk):
    """
    GET: Retrieve test details
    PUT/PATCH: Update test (Admin only)
    DELETE: Delete test (Admin only)
    """
    try:
        test = Test.objects.get(_id=ObjectId(pk))
        
        if request.user.role != 'admin' and test.candidate != request.user:
            return Response({
                'success': False,
                'message': 'You do not have permission to access this test'
            }, status=status.HTTP_403_FORBIDDEN)
            
    except Test.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Test not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        serializer = TestDetailSerializer(test)
        return safe_response({
            'success': True,
            'data': serializer.data
        })
    
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'message': 'Admin permission required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method in ['PUT', 'PATCH']:
        serializer = TestSerializer(test, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return safe_response({
                'success': True,
                'message': 'Test updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        test.delete()
        return Response({
            'success': True,
            'message': 'Test deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_start(request, pk):
    """Start the test - Allow all authenticated users"""
    try:
        test = None
        
        # Check if it's an ObjectId (24 characters, hex)
        if len(pk) == 24 and all(c in '0123456789abcdefABCDEF' for c in pk):
            try:
                test = Test.objects.get(_id=ObjectId(pk))
                print(f"Found test by ObjectId: {pk}")
            except (InvalidId, Test.DoesNotExist):
                return Response({
                    'success': False,
                    'message': 'Test not found'
                }, status=404)
        else:
            # Try as UUID
            try:
                # Remove hyphens if present and convert to UUID
                clean_pk = pk.replace('-', '')
                test_uuid = uuid.UUID(clean_pk)
                test = Test.objects.get(_id=test_uuid)
                print(f"Found test by UUID: {pk}")
            except (ValueError, Test.DoesNotExist):
                return Response({
                    'success': False,
                    'message': 'Test not found'
                }, status=404)
        
        # ✅ ALLOW ALL authenticated users - no permission checks
        print(f"Access granted to {request.user.email}")
        
        # Check test status
        if test.status != 'pending':
            return Response({
                'success': False,
                'message': f'Test is already {test.status}'
            }, status=400)
        
        # Start the test
        test.start()
        
        serializer = TestDetailSerializer(test)
        return Response({
            'success': True,
            'message': 'Test started successfully',
            'data': serializer.data
        })
        
    except Exception as e:
        print(f"Error in test_start: {str(e)}")
        return Response({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
    
# @api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])
# def test_submit(request, pk):
#     """Submit test answers"""
#     try:
#         test = Test.objects.get(_id=ObjectId(pk))
#     except Test.DoesNotExist:
#         return Response({
#             'success': False,
#             'message': 'Test not found'
#         }, status=404)
    
#     print(f"User: {request.user.email}, Role: {request.user.role}, ID: {request.user.id}")
#     print(f"Test candidate_id: {test.candidate_id}, Test candidate: {test.candidate}")
#     print(f"Test status: {test.status}")
    
#     is_admin = request.user.role == 'admin'
#     is_owner = str(test.candidate_id) == str(request.user.id)
    
#     print(f"is_admin: {is_admin}, is_owner: {is_owner}")
    
#     # FIX: Reassign test if user is candidate and test doesn't have the right candidate
#     # This will work regardless of test status
#     if not (is_admin or is_owner) and request.user.role == 'candidate':
#         print(f"Reassigning test from {test.candidate} to {request.user}")
#         test.candidate = request.user
#         test.save()
#         is_owner = True  # Now the user owns the test
#         print(f"Test reassigned. New owner: {request.user.email}")
    
#     if not (is_admin or is_owner):
#         return Response({
#             'success': False,
#             'message': 'Permission denied. You are not authorized to submit this test.'
#         }, status=403)
    
#     # Check test status
#     if test.status != 'in_progress':
#         return Response({
#             'success': False,
#             'message': f'Test cannot be submitted. Current status: {test.status}'
#         }, status=400)
    
#     if test.is_expired():
#         test.status = 'expired'
#         test.save()
#         return Response({
#             'success': False,
#             'message': 'Test expired'
#         }, status=400)
    
#     answers = request.data.get('answers', {})
#     test.complete(answers)
    
#     return Response({
#         'success': True,
#         'message': 'Test submitted successfully',
#         'data': {
#             'test_id': test.test_id,
#             'status': test.status,
#             'percentage': test.percentage,
#             'passed': test.passed,
#             'total_marks': test.total_marks,
#             'obtained_marks': test.obtained_marks
#         }
#     })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_submit(request, pk):
    """Submit test answers"""
    try:
        test = Test.objects.get(_id=ObjectId(pk))
    except Test.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Test not found'
        }, status=404)
    
    print(f"User: {request.user.email}, Role: {request.user.role}, ID: {request.user.id}")
    print(f"Test candidate_id: {test.candidate_id}, Test candidate: {test.candidate}")
    print(f"Test status: {test.status}")
    
    is_admin = request.user.role == 'admin'
    is_owner = str(test.candidate_id) == str(request.user.id)
    
    # Reassign test if needed
    if not (is_admin or is_owner) and request.user.role == 'candidate':
        print(f"Reassigning test from {test.candidate} to {request.user}")
        if test.status == 'in_progress':
            test.status = 'pending'
            test.start_time = None
        test.candidate = request.user
        test.save()
        is_owner = True
    
    if not (is_admin or is_owner):
        return Response({
            'success': False,
            'message': 'Permission denied. You are not authorized to submit this test.'
        }, status=403)
    
    if test.status != 'in_progress':
        return Response({
            'success': False,
            'message': f'Test cannot be submitted. Current status: {test.status}'
        }, status=400)
    
    if test.is_expired():
        test.status = 'expired'
        test.save()
        return Response({
            'success': False,
            'message': 'Test expired'
        }, status=400)
    
    # Get and process answers
    answers = request.data.get('answers', {})
    
    # Ensure answers is a dictionary with string keys
    processed_answers = {}
    if isinstance(answers, dict):
        for key, value in answers.items():
            processed_answers[str(key)] = value
    elif isinstance(answers, list):
        # If answers is a list, map to question IDs
        questions = test.get_all_questions()
        for i, ans in enumerate(answers):
            if i < len(questions) and ans is not None:
                q_id = str(questions[i].get('_id', questions[i].get('id', '')))
                if q_id:
                    processed_answers[q_id] = ans
    
    print(f"Processed answers: {processed_answers}")
    
    # Complete the test
    test.complete(processed_answers)
    
    # Refresh to get updated values
    test.refresh_from_db()
    
    return Response({
        'success': True,
        'message': 'Test submitted successfully',
        'data': {
            'test_id': test.test_id,
            'status': test.status,
            'percentage': float(test.percentage),
            'passed': bool(test.passed),
            'total_marks': int(test.total_marks),
            'obtained_marks': int(test.obtained_marks)
        }
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrAdmin])
def test_questions(request, pk):
    """Get test questions (for test taking)"""
    try:
        test = Test.objects.get(_id=ObjectId(pk))
        
        if request.user.role != 'admin' and test.candidate != request.user:
            return Response({
                'success': False,
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
            
    except Test.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Test not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if test.status == 'pending':
        return Response({
            'success': False,
            'message': 'Test not started yet'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if test.status == 'completed':
        return Response({
            'success': False,
            'message': 'Test already completed'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from django.utils import timezone
    
    if test.start_time and test.status == 'in_progress':
        elapsed = (timezone.now() - test.start_time).total_seconds() / 60
        if elapsed > test.duration_minutes:
            test.status = 'expired'
            test.save()
            return Response({
                'success': False,
                'message': 'Test has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        remaining_seconds = max(0, int((test.duration_minutes * 60) - (timezone.now() - test.start_time).total_seconds()))
    else:
        remaining_seconds = 0
    
    questions = test.get_all_questions()
    for q in questions:
        if 'correct_answer' in q:
            del q['correct_answer']
        if 'explanation' in q:
            del q['explanation']
    
    return Response({
        'success': True,
        'data': {
            'test_id': str(test._id),
            'duration_minutes': test.duration_minutes,
            'remaining_seconds': remaining_seconds,
            'questions': questions
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrAdmin])
def test_save_answer(request, pk):
    """Save answer for a question"""
    try:
        test = Test.objects.get(_id=ObjectId(pk))
        
        if request.user.role != 'admin' and test.candidate != request.user:
            return Response({
                'success': False,
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
            
    except Test.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Test not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if test.status != 'in_progress':
        return Response({
            'success': False,
            'message': 'Test is not in progress'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if test.is_expired():
        test.expire()
        return Response({
            'success': False,
            'message': 'Test has expired'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    question_id = request.data.get('question_id')
    answer = request.data.get('answer')
    
    if not question_id or answer is None:
        return Response({
            'success': False,
            'message': 'question_id and answer are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not isinstance(answer, int) or answer < 0 or answer > 3:
        return Response({
            'success': False,
            'message': 'Answer must be between 0 and 3'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not test.answers:
        test.answers = {}
    test.answers[question_id] = answer
    test.save(update_fields=['answers'])
    
    return Response({
        'success': True,
        'message': 'Answer saved successfully'
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrAdmin])
def test_result(request, pk):
    """Get test result"""
    try:
        test = Test.objects.get(_id=ObjectId(pk))
        
        if request.user.role != 'admin' and test.candidate != request.user:
            return Response({
                'success': False,
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
            
    except Test.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Test not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if test.status != 'completed':
        return Response({
            'success': False,
            'message': 'Test not completed yet'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    questions = test.get_all_questions()
    question_results = []
    
    # Initialize category_wise with all possible categories
    category_wise = {
        'aptitude': {'total': 0, 'correct': 0},
        'technical': {'total': 0, 'correct': 0},
        'logical': {'total': 0, 'correct': 0},
        'verbal': {'total': 0, 'correct': 0}
    }
    
    technology_wise = {}
    
    for q in questions:
        q_id = str(q.get('_id', q.get('id', '')))
        selected_data = test.answers.get(q_id)
        
        # Extract the selected_option value
        selected_value = None
        if selected_data is not None:
            if isinstance(selected_data, dict):
                selected_value = selected_data.get('selected_option')
                if selected_value is None and selected_data:
                    first_key = next(iter(selected_data))
                    if first_key != 'time_spent':
                        selected_value = selected_data[first_key]
            else:
                selected_value = selected_data
        
        # Get correct answer
        correct = q.get('correct_answer') or q.get('correct') or q.get('answer')
        
        # Get category
        category = q.get('category', 'technical')
        if category not in category_wise:
            category_wise[category] = {'total': 0, 'correct': 0}
        
        # Get technology for technical questions
        technology = q.get('technology') or q.get('tech') or 'general'
        
        marks_obtained = 0
        is_correct = False
        
        # Compare selected value with correct answer
        if selected_value is not None and correct is not None:
            try:
                if isinstance(selected_value, (int, float)) or str(selected_value).isdigit():
                    selected_int = int(selected_value)
                    correct_int = int(correct) if str(correct).isdigit() else correct
                    if selected_int == correct_int:
                        marks_obtained = q.get('marks', 1)
                        is_correct = True
                elif str(selected_value).strip().lower() == str(correct).strip().lower():
                    marks_obtained = q.get('marks', 1)
                    is_correct = True
            except:
                pass
        
        # Update category counts
        category_wise[category]['total'] += 1
        if is_correct:
            category_wise[category]['correct'] += 1
        
        # Update technology counts
        if category == 'technical' and technology:
            if technology not in technology_wise:
                technology_wise[technology] = {'total': 0, 'correct': 0}
            technology_wise[technology]['total'] += 1
            if is_correct:
                technology_wise[technology]['correct'] += 1
        
        # ✅ Get question text without truncation for full view
        question_text = q.get('text', q.get('question_text', ''))
        
        question_results.append({
            'id': q_id,
            'text': question_text,  # Full text
            'text_preview': question_text[:100] + '...' if len(question_text) > 100 else question_text,  # Preview
            'selected': selected_value,
            'correct': correct,
            'marks_obtained': marks_obtained,
            'is_correct': is_correct,
            'status': 'Correct' if is_correct else 'Wrong',  # ✅ Add status field
            'category': category,
            'technology': technology if category == 'technical' else None,
            'options': q.get('options', [])  # Include options for reference
        })
    
    # Calculate totals
    total_correct = sum(1 for qr in question_results if qr['is_correct'])
    total_marks_obtained = sum(qr['marks_obtained'] for qr in question_results)
    
    # Remove empty categories
    category_wise = {k: v for k, v in category_wise.items() if v['total'] > 0}
    
    # ✅ Add summary statistics
    correct_count = total_correct
    wrong_count = len(questions) - total_correct
    
    return Response({
        'success': True,
        'data': {
            'test_id': test.test_id,
            'candidate': test.candidate.name if test.candidate else None,
            'experience_level': test.experience_level,
            'selected_technologies': test.selected_technologies,
            'total_questions': len(questions),
            'attempted': len([qr for qr in question_results if qr['selected'] is not None]),
            'correct': total_correct,
            'wrong': wrong_count,  # ✅ Add wrong count
            'not_attempted': len([qr for qr in question_results if qr['selected'] is None]),
            'total_marks': test.total_marks or len(questions),
            'obtained_marks': total_marks_obtained,
            'percentage': (total_correct / len(questions) * 100) if questions else 0,
            'passed': (total_correct / len(questions) * 100) >= 70 if questions else False,
            'category_wise': category_wise,
            'technology_wise': technology_wise,
            'question_results': question_results,
            'summary': {  # ✅ Add summary section
                'correct_count': correct_count,
                'wrong_count': wrong_count,
                'correct_percentage': round((correct_count / len(questions) * 100), 2) if questions else 0,
                'wrong_percentage': round((wrong_count / len(questions) * 100), 2) if questions else 0
            }
        }
    })

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def test_stats(request):
    """Get test statistics (Admin only)"""
    total_tests = Test.objects.count()
    pending = Test.objects.filter(status='pending').count()
    in_progress = Test.objects.filter(status='in_progress').count()
    completed = Test.objects.filter(status='completed').count()
    expired = Test.objects.filter(status='expired').count()
    
    passed = Test.objects.filter(status='completed', passed=True).count()
    failed = Test.objects.filter(status='completed', passed=False).count()
    
    return safe_response({
        'success': True,
        'data': {
            'total': total_tests,
            'by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'completed': completed,
                'expired': expired
            },
            'results': {
                'passed': passed,
                'failed': failed,
                'pass_rate': (passed / completed * 100) if completed > 0 else 0
            }
        }
    })

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from services.ai_service import TestGenerator
from .models import Test
from .serializers import TestSerializer
import json

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_ai_test(request):
    """
    Generate AI-powered test for user
    POST /api/tests/generate-ai-test/
    
    {
        "experience_level": "junior",
        "technologies": ["python", "django"],
        "num_aptitude": 10,
        "num_technical": 10
    }
    """
    data = request.data
    
    experience_level = data.get('experience_level')
    technologies = data.get('technologies', [])
    num_aptitude = data.get('num_aptitude', 10)
    num_technical = data.get('num_technical', 10)
    
    if not experience_level:
        return Response({
            'success': False,
            'message': 'experience_level is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not technologies:
        return Response({
            'success': False,
            'message': 'technologies is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    test_data = TestGenerator.generate_test(
        user=request.user,
        experience_level=experience_level,
        technologies=technologies,
        num_aptitude=num_aptitude,
        num_technical=num_technical
    )
    
    test = Test.objects.create(
        user=request.user,
        experience_level=experience_level,
        technologies=technologies,
        aptitude_questions=test_data['aptitude_questions'],
        technical_questions=test_data['technical_questions'],
        total_questions=num_aptitude + (num_technical * len(technologies))
    )
    
    return Response({
        'success': True,
        'message': 'Test generated successfully',
        'data': {
            'test_id': str(test.id),
            'experience_level': experience_level,
            'technologies': technologies,
            'aptitude_questions': test_data['aptitude_questions'],
            'technical_questions': test_data['technical_questions']
        }
    })


import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_test_results(request):
    """
    Admin API to view all test results with filtering options
    """
    try:
        # Log the request
        logger.info(f"Admin test results request from user: {request.user.email}")
        logger.info(f"Query params: {request.query_params}")
        
        # Get query parameters
        candidate_id = request.query_params.get('candidate_id')
        status_filter = request.query_params.get('status')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        experience_level = request.query_params.get('experience_level')
        technology = request.query_params.get('technology')
        
        # Pagination parameters
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        # Base queryset
        tests = Test.objects.all().order_by('-created_at')
        logger.info(f"Total tests before filtering: {tests.count()}")
        
        # Apply filters
        if candidate_id:
            tests = tests.filter(candidate_id=candidate_id)
            logger.info(f"After candidate filter: {tests.count()}")
        
        if status_filter:
            tests = tests.filter(status=status_filter)
            logger.info(f"After status filter: {tests.count()}")
        
        if from_date:
            tests = tests.filter(created_at__gte=datetime.fromisoformat(from_date))
            logger.info(f"After from_date filter: {tests.count()}")
        
        if to_date:
            tests = tests.filter(created_at__lte=datetime.fromisoformat(to_date))
            logger.info(f"After to_date filter: {tests.count()}")
        
        if experience_level:
            tests = tests.filter(experience_level=experience_level)
            logger.info(f"After experience filter: {tests.count()}")
        
        # FIXED: Handle technology filtering properly for MongoDB
        if technology and technology.strip():
            logger.info(f"Applying technology filter: {technology}")
            
            # Option 1: Use __icontains for partial matching (works with Djongo)
            try:
                tests = tests.filter(selected_technologies__icontains=technology)
                logger.info(f"After technology filter (icontains): {tests.count()}")
            except Exception as e:
                logger.error(f"Error with icontains filter: {e}")
                
                # Option 2: Fallback to in-memory filtering
                logger.info("Falling back to in-memory filtering")
                test_ids = []
                for test in tests:
                    if hasattr(test, 'selected_technologies') and test.selected_technologies:
                        techs = [str(t).lower() for t in test.selected_technologies]
                        if technology.lower() in techs:
                            test_ids.append(test.id)
                
                tests = tests.filter(id__in=test_ids)
                logger.info(f"After technology filter (in-memory): {tests.count()}")
        
        # Get total count before pagination
        total_count = tests.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tests = tests[start:end]
        
        # Process paginated tests
        test_results = []
        
        for test in paginated_tests:
            try:
                logger.info(f"Processing test ID: {test.test_id}")
                
                questions = test.get_all_questions()
                logger.info(f"Test {test.test_id} has {len(questions)} questions")
                
                # Helper function to extract selected value
                def get_selected_value(answer):
                    if answer is None:
                        return None
                    if isinstance(answer, dict):
                        return answer.get('selected_option')
                    return answer
                
                # Calculate statistics
                total_questions = len(questions)
                attempted = len(test.answers) if test.answers else 0
                
                correct = 0
                total_obtained_marks = 0
                
                if test.answers:
                    for q in questions:
                        q_id = str(q.get('_id', q.get('id', '')))
                        if q_id in test.answers:
                            selected = test.answers[q_id]
                            selected_value = get_selected_value(selected)
                            correct_answer = q.get('correct_answer')
                            
                            if selected_value is not None and selected_value == correct_answer:
                                correct += 1
                                total_obtained_marks += q.get('marks', 1)
                
                # Calculate percentage
                percentage = (correct / total_questions * 100) if total_questions > 0 else 0
                
                # Category wise analysis
                category_wise = {
                    'aptitude': {'total': 0, 'correct': 0},
                    'technical': {'total': 0, 'correct': 0}
                }
                
                technology_wise = {}
                
                for q in questions:
                    category = q.get('category', 'technical')
                    tech = q.get('technology', 'unknown')
                    q_id = str(q.get('_id', q.get('id', '')))
                    selected = test.answers.get(q_id) if test.answers else None
                    selected_value = get_selected_value(selected)
                    correct_answer = q.get('correct_answer')
                    
                    if category in category_wise:
                        category_wise[category]['total'] += 1
                        if selected_value is not None and selected_value == correct_answer:
                            category_wise[category]['correct'] += 1
                    
                    if category == 'technical':
                        if tech not in technology_wise:
                            technology_wise[tech] = {'total': 0, 'correct': 0}
                        technology_wise[tech]['total'] += 1
                        if selected_value is not None and selected_value == correct_answer:
                            technology_wise[tech]['correct'] += 1
                
                # FIX: Handle completed_at properly
                completed_at = None
                if test.status == 'completed':
                    # Try to get completed_at from different possible fields
                    if hasattr(test, 'completed_at') and test.completed_at:
                        completed_at = test.completed_at
                    elif hasattr(test, 'updated_at'):
                        # If no completed_at, use updated_at as fallback
                        completed_at = test.updated_at
                    elif hasattr(test, 'end_time') and test.end_time:
                        completed_at = test.end_time
                
                # Format dates safely
                created_at_iso = test.created_at.isoformat() if test.created_at else None
                completed_at_iso = completed_at.isoformat() if completed_at else None
                
                test_results.append({
                    'test_id': test.test_id,
                    'candidate': {
                        'id': str(test.candidate.id) if test.candidate else None,
                        'name': test.candidate.name if test.candidate else None,
                        'email': test.candidate.email if test.candidate else None,
                    } if test.candidate else None,
                    'status': test.status,
                    'experience_level': test.experience_level,
                    'selected_technologies': test.selected_technologies,
                    'created_at': created_at_iso,
                    'completed_at': completed_at_iso,
                    'stats': {
                        'total_questions': total_questions,
                        'attempted': attempted,
                        'correct': correct,
                        'total_marks': float(test.total_marks) if test.total_marks else float(total_questions),
                        'obtained_marks': float(total_obtained_marks),
                        'percentage': float(percentage),
                        'passed': percentage >= 70,
                    },
                    'category_wise': category_wise,
                    'technology_wise': technology_wise,
                    'summary': f"{correct}/{total_questions} correct - {percentage:.1f}%" if total_questions > 0 else "No questions"
                })
                
                logger.info(f"Successfully processed test {test.test_id}")
                
            except Exception as e:
                logger.error(f"Error processing test {test.test_id}: {str(e)}")
                logger.error(traceback.format_exc())
                continue
        
        # Calculate overall statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for t in test_results if t['stats']['passed'])
        
        response_data = {
            'success': True,
            'data': {
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'page_size': page_size,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'pass_percentage': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'results': test_results
            }
        }
        
        logger.info(f"Returning {total_tests} test results")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error in admin_test_results: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': f"Error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_test_detail(request, test_id):
    """
    Admin API to view detailed result of a specific test
    """
    try:
        test = Test.objects.get(test_id=test_id)
        
        questions = test.get_all_questions()
        question_results = []
        
        for q in questions:
            q_id = str(q.get('_id', q.get('id', '')))
            selected = test.answers.get(q_id) if test.answers else None
            correct = q.get('correct_answer')
            marks_obtained = 0
            
            if selected is not None and selected == correct:
                marks_obtained = q.get('marks', 1)
            
            question_results.append({
                'id': q_id,
                'text': q.get('text', ''),
                'options': q.get('options', []),
                'selected': selected,
                'correct': correct,
                'marks': q.get('marks', 1),
                'marks_obtained': marks_obtained,
                'is_correct': selected == correct,
                'category': q.get('category', 'technical'),
                'technology': q.get('technology', 'unknown'),
                'difficulty': q.get('difficulty', 'medium')
            })
        
        # Category wise analysis
        category_wise = {
            'aptitude': {'total': 0, 'correct': 0, 'marks': 0, 'obtained': 0},
            'technical': {'total': 0, 'correct': 0, 'marks': 0, 'obtained': 0}
        }
        
        technology_wise = {}
        
        for q in questions:
            category = q.get('category', 'technical')
            tech = q.get('technology', 'unknown')
            q_id = str(q.get('_id', q.get('id', '')))
            selected = test.answers.get(q_id) if test.answers else None
            correct = q.get('correct_answer')
            marks = q.get('marks', 1)
            
            if category in category_wise:
                category_wise[category]['total'] += 1
                category_wise[category]['marks'] += marks
                if selected is not None and selected == correct:
                    category_wise[category]['correct'] += 1
                    category_wise[category]['obtained'] += marks
            
            if category == 'technical':
                if tech not in technology_wise:
                    technology_wise[tech] = {
                        'total': 0, 
                        'correct': 0, 
                        'marks': 0, 
                        'obtained': 0
                    }
                technology_wise[tech]['total'] += 1
                technology_wise[tech]['marks'] += marks
                if selected is not None and selected == correct:
                    technology_wise[tech]['correct'] += 1
                    technology_wise[tech]['obtained'] += marks
        
        return safe_response({
            'success': True,
            'data': {
                'test': {
                    'test_id': test.test_id,
                    'candidate': {
                        'id': test.candidate.id if test.candidate else None,
                        'name': test.candidate.name if test.candidate else None,
                        'email': test.candidate.email if test.candidate else None,
                    } if test.candidate else None,
                    'status': test.status,
                    'experience_level': test.experience_level,
                    'selected_technologies': test.selected_technologies,
                    'created_at': test.created_at,
                    'started_at': test.started_at,
                    'completed_at': test.completed_at,
                    'total_time': test.total_time,
                    'time_taken': test.time_taken,
                },
                'summary': {
                    'total_questions': len(questions),
                    'attempted': len(test.answers) if test.answers else 0,
                    'correct': sum(1 for q in question_results if q['is_correct']),
                    'total_marks': test.total_marks,
                    'obtained_marks': test.obtained_marks,
                    'percentage': test.percentage,
                    'passed': test.passed,
                },
                'category_wise': category_wise,
                'technology_wise': technology_wise,
                'questions': question_results
            }
        })
        
    except Test.DoesNotExist:
        return safe_response({
            'success': False,
            'message': 'Test not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return safe_response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# @permission_classes([permissions.IsAuthenticated, IsAdminOnly])
# def admin_candidate_test_history(request, candidate_id):
#     """
#     Admin API to view test history of a specific candidate
#     """
#     try:
#         from django.contrib.auth import get_user_model
#         User = get_user_model()
        
#         candidate = User.objects.get(id=candidate_id)
#         tests = Test.objects.filter(candidate=candidate).order_by('-created_at')
        
#         test_history = []
        
#         for test in tests:
#             questions = test.get_all_questions()
#             total_questions = len(questions)
#             attempted = len(test.answers) if test.answers else 0
            
#             correct = 0
#             if test.answers:
#                 for q in questions:
#                     q_id = str(q.get('_id', q.get('id', '')))
#                     if q_id in test.answers and test.answers[q_id] == q.get('correct_answer'):
#                         correct += 1
            
#             test_history.append({
#                 'test_id': test.test_id,
#                 'status': test.status,
#                 'experience_level': test.experience_level,
#                 'selected_technologies': test.selected_technologies,
#                 'created_at': test.created_at,
#                 'completed_at': test.completed_at,
#                 'total_questions': total_questions,
#                 'attempted': attempted,
#                 'correct': correct,
#                 'total_marks': test.total_marks,
#                 'obtained_marks': test.obtained_marks,
#                 'percentage': test.percentage,
#                 'passed': test.passed,
#             })
        
#         # Calculate overall stats
#         completed_tests = [t for t in test_history if t['status'] == 'completed']
#         passed_tests = [t for t in completed_tests if t['passed']]
        
#         return safe_response({
#             'success': True,
#             'data': {
#                 'candidate': {
#                     'id': candidate.id,
#                     'name': candidate.name,
#                     'email': candidate.email,
#                 },
#                 'stats': {
#                     'total_tests': len(test_history),
#                     'completed_tests': len(completed_tests),
#                     'passed_tests': len(passed_tests),
#                     'pass_percentage': (len(passed_tests) / len(completed_tests) * 100) if completed_tests else 0,
#                     'avg_percentage': sum(t['percentage'] for t in completed_tests) / len(completed_tests) if completed_tests else 0,
#                 },
#                 'test_history': test_history
#             }
#         })
        
#     except User.DoesNotExist:
#         return safe_response({
#             'success': False,
#             'message': 'Candidate not found'
#         }, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return safe_response({
#             'success': False,
#             'message': str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_test_statistics(request):
    """
    Admin API to get overall test statistics
    """
    try:
        from datetime import datetime, timedelta
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        from_date = datetime.now() - timedelta(days=days)
        
        # Get all tests in date range
        tests = Test.objects.filter(created_at__gte=from_date)
        
        # Basic stats
        total_tests = tests.count()
        completed_tests = tests.filter(status='completed').count()
        pending_tests = tests.filter(status='pending').count()
        in_progress_tests = tests.filter(status='in_progress').count()
        
        completed = tests.filter(status='completed')
        passed_tests = completed.filter(passed=True).count()
        
        # Daily trends
        daily_tests = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date()
            daily_tests[date.isoformat()] = {
                'total': 0,
                'completed': 0,
                'passed': 0
            }
        
        for test in tests:
            date = test.created_at.date().isoformat()
            if date in daily_tests:
                daily_tests[date]['total'] += 1
                if test.status == 'completed':
                    daily_tests[date]['completed'] += 1
                    if test.passed:
                        daily_tests[date]['passed'] += 1
        
        # Technology wise stats
        tech_stats = {}
        for test in tests:
            for tech in test.selected_technologies:
                if tech not in tech_stats:
                    tech_stats[tech] = {'total': 0, 'passed': 0}
                tech_stats[tech]['total'] += 1
                if test.status == 'completed' and test.passed:
                    tech_stats[tech]['passed'] += 1
        
        return safe_response({
            'success': True,
            'data': {
                'period': f'Last {days} days',
                'overall': {
                    'total_tests': total_tests,
                    'completed_tests': completed_tests,
                    'pending_tests': pending_tests,
                    'in_progress_tests': in_progress_tests,
                    'passed_tests': passed_tests,
                    'pass_percentage': (passed_tests / completed_tests * 100) if completed_tests > 0 else 0,
                },
                'daily_trends': daily_tests,
                'technology_wise': tech_stats
            }
        })
        
    except Exception as e:
        return safe_response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)