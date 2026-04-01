from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from bson import ObjectId
from django.core.paginator import Paginator
from bson import ObjectId
from bson.errors import InvalidId
from .models import QuestionBank
from .serializers import QuestionBankSerializer
from questions.models import Question
from questions.serializers import QuestionSerializer
from core.permissions import IsAdmin

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def question_bank_list(request):
    """
    GET: List all question banks (with filters and pagination)
    POST: Create new question bank (Admin only)
    """
    if request.method == 'GET':
        queryset = QuestionBank.objects.all().order_by('-created_at')
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        technology = request.query_params.get('technology')
        if technology:
            queryset = queryset.filter(technologies__contains=technology)
        
        level = request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        
        serializer = QuestionBankSerializer(current_page, many=True)
        
        return Response({
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
        })
    
    elif request.method == 'POST':
        if not request.user.is_staff:
            return Response({
                'success': False,
                'message': 'Admin permission required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = QuestionBankSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response({
                'success': True,
                'message': 'Question bank created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def question_bank_detail(request, pk):
    """
    GET: Retrieve question bank
    PUT/PATCH: Update question bank (Admin only)
    DELETE: Delete question bank (Admin only)
    """
    try:
        try:
            if len(str(pk)) == 24:
                obj_id = ObjectId(pk)
                question_bank = QuestionBank.objects.get(_id=obj_id)
            else:
                question_bank = QuestionBank.objects.get(_id=pk)
        except InvalidId:
            question_bank = QuestionBank.objects.get(_id=pk)
        
        if not question_bank.is_active:
            return Response({
                'success': False,
                'message': 'Question bank is inactive'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except QuestionBank.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Question bank with ID {pk} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        serializer = QuestionBankSerializer(question_bank)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    if not request.user.is_staff:
        return Response({
            'success': False,
            'message': 'Admin permission required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'PUT':
        serializer = QuestionBankSerializer(question_bank, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Question bank updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PATCH':
        serializer = QuestionBankSerializer(question_bank, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Question bank updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        question_bank.is_active = False
        question_bank.save()
        return Response({
            'success': True,
            'message': 'Question bank deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdmin])
def question_bank_add_questions(request, pk):
    """Add questions to bank"""
    try:
        try:
            if len(str(pk)) == 24:
                obj_id = ObjectId(pk)
                bank = QuestionBank.objects.get(_id=obj_id)
            else:
                bank = QuestionBank.objects.get(_id=pk)
        except InvalidId:
            bank = QuestionBank.objects.get(_id=pk)

        if not bank.is_active:
            return Response({
                'success': False,
                'message': 'Question bank is inactive'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except QuestionBank.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Question bank with ID {pk} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    question_ids = request.data.get('question_ids', [])
    
    if not question_ids or not isinstance(question_ids, list):
        return Response({
            'success': False,
            'message': 'question_ids must be a list'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    existing = bank.questions or []  
    new_ids = []
    invalid_ids = []
    duplicate_ids = []
    
    for q_id in question_ids:
        try:
            if isinstance(q_id, str):
                try:
                    if len(q_id) == 24:
                        q_obj = ObjectId(q_id)
                    else:
                        q_obj = q_id
                except:
                    q_obj = q_id
            else:
                q_obj = q_id
            
            question = Question.objects.filter(_id=q_obj).first()
            if not question:
                question = Question.objects.filter(_id=str(q_obj)).first()
            
            if question:
                if q_id not in existing and str(q_obj) not in [str(x) for x in existing]:
                    new_ids.append(q_id)
                else:
                    duplicate_ids.append(str(q_id))
            else:
                invalid_ids.append(str(q_id))
                
        except Exception as e:
            invalid_ids.append(str(q_id))
    
    if invalid_ids:
        return Response({
            'success': False,
            'message': 'Invalid question IDs',
            'invalid_ids': invalid_ids
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_ids:
        bank.questions.extend(new_ids)
        bank.save()
    
    serializer = QuestionBankSerializer(bank)
    return Response({
        'success': True,
        'message': f'{len(new_ids)} questions added',
        'data': {
            'added': len(new_ids),
            'duplicates': len(duplicate_ids),
            'bank': serializer.data
        }
    })

@api_view(['POST'])
@permission_classes([IsAdmin])
def question_bank_remove_questions(request, pk):
    """Remove questions from bank"""
    try:
        try:
            if len(str(pk)) == 24:
                obj_id = ObjectId(pk)
                bank = QuestionBank.objects.get(_id=obj_id)
            else:
                bank = QuestionBank.objects.get(_id=pk)
        except InvalidId:
            bank = QuestionBank.objects.get(_id=pk)
            
    except QuestionBank.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Question bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    question_ids = request.data.get('question_ids', [])
    
    if not question_ids or not isinstance(question_ids, list):
        return Response({
            'success': False,
            'message': 'question_ids must be a list'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    ids_to_remove = [str(q_id) for q_id in question_ids]
    
    original_count = len(bank.questions or [])
    bank.questions = [q for q in (bank.questions or []) if str(q) not in ids_to_remove]
    removed_count = original_count - len(bank.questions)
    
    if removed_count > 0:
        bank.save()
    
    serializer = QuestionBankSerializer(bank)
    return Response({
        'success': True,
        'message': f'{removed_count} questions removed',
        'data': {
            'removed': removed_count,
            'bank': serializer.data
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def question_bank_questions(request, pk):
    """Get paginated questions in bank"""
    try:
        try:
            if len(str(pk)) == 24:
                obj_id = ObjectId(pk)
                bank = QuestionBank.objects.get(_id=obj_id)
            else:
                bank = QuestionBank.objects.get(_id=pk)
        except InvalidId:
            bank = QuestionBank.objects.get(_id=pk)
            
    except QuestionBank.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Question bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    
    question_ids = bank.questions or []
    total = len(question_ids)
    
    start = (page - 1) * page_size
    end = start + page_size
    paginated_ids = question_ids[start:end]
    
    questions = []
    for q_id in paginated_ids:
        try:
            q_id_str = str(q_id)
            if len(q_id_str) == 24:
                try:
                    question = Question.objects.filter(_id=ObjectId(q_id_str)).first()
                except:
                    question = Question.objects.filter(_id=q_id_str).first()
            else:
                question = Question.objects.filter(_id=q_id_str).first()
            
            if question:
                questions.append(question)
        except:
            continue
    
    q_type = request.query_params.get('type')
    if q_type:
        questions = [q for q in questions if getattr(q, 'question_type', '') == q_type]
    
    difficulty = request.query_params.get('difficulty')
    if difficulty:
        questions = [q for q in questions if getattr(q, 'difficulty', '') == difficulty]
    
    serializer = QuestionSerializer(questions, many=True)
    
    return Response({
        'success': True,
        'data': {
            'bank_id': pk,
            'bank_name': bank.name,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total > 0 else 0,
            'questions': serializer.data
        }
    })


from bson import ObjectId
from bson.errors import InvalidId

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def question_bank_stats(request, pk):
    """Get statistics about questions in bank"""
    try:
        try:
            if len(str(pk)) == 24:
                obj_id = ObjectId(pk)
                bank = QuestionBank.objects.get(_id=obj_id)
            else:
                bank = QuestionBank.objects.get(_id=pk)
        except InvalidId:
            bank = QuestionBank.objects.get(_id=pk)
        
        if not bank.is_active:
            return Response({
                'success': False,
                'message': 'Question bank is inactive'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except QuestionBank.DoesNotExist:
        return Response({
            'success': False,
            'message': f'Question bank with ID {pk} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    question_ids = bank.questions or []
    
    if not question_ids:
        return Response({
            'success': True,
            'data': {
                'total_questions': 0,
                'total_marks': 0,
                'avg_marks': 0,
                'by_type': {},
                'by_difficulty': {}
            }
        })
    
    questions = []
    for q_id in question_ids:
        try:
            question = None
            if isinstance(q_id, str):
                try:
                    if len(q_id) == 24:
                        question = Question.objects.filter(_id=ObjectId(q_id)).first()
                    else:
                        question = Question.objects.filter(_id=q_id).first()
                except:
                    question = Question.objects.filter(_id=q_id).first()
            else:
                question = Question.objects.filter(_id=q_id).first()
            
            if question:
                questions.append(question)
        except:
            continue
    
    total_marks = sum(q.marks for q in questions)
    
    type_stats = {}
    for q in questions:
        q_type = getattr(q, 'question_type', 'unknown')
        if q_type not in type_stats:
            type_stats[q_type] = {'count': 0, 'marks': 0}
        type_stats[q_type]['count'] += 1
        type_stats[q_type]['marks'] += q.marks
    
    difficulty_stats = {}
    for q in questions:
        diff = getattr(q, 'difficulty', 'medium')
        difficulty_stats[diff] = difficulty_stats.get(diff, 0) + 1
    
    return Response({
        'success': True,
        'data': {
            'bank_id': str(bank._id),
            'bank_name': bank.name,
            'total_questions': len(questions),
            'total_marks': total_marks,
            'avg_marks': round(total_marks / len(questions), 2) if questions else 0,
            'by_type': type_stats,
            'by_difficulty': difficulty_stats
        }
    })

@api_view(['POST'])
@permission_classes([IsAdmin])
def question_bank_bulk_add_questions(request, pk):
    """Bulk add questions using filters"""
    try:
        try:
            if len(str(pk)) == 24:
                obj_id = ObjectId(pk)
                bank = QuestionBank.objects.get(_id=obj_id)
            else:
                bank = QuestionBank.objects.get(_id=pk)
        except InvalidId:
            bank = QuestionBank.objects.get(_id=pk)
            
    except QuestionBank.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Question bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    filters = request.data.get('filters', {})
    limit = request.data.get('limit', 100)
    
    query = Q()
    if filters.get('question_type'):
        query &= Q(question_type=filters['question_type'])
    if filters.get('difficulty'):
        query &= Q(difficulty=filters['difficulty'])
    if filters.get('technology'):
        query &= Q(technology=filters['technology'])
    if filters.get('min_marks'):
        query &= Q(marks__gte=filters['min_marks'])
    if filters.get('max_marks'):
        query &= Q(marks__lte=filters['max_marks'])
    
    existing_ids = [str(q) for q in (bank.questions or [])]
    
    questions = Question.objects.filter(query).exclude(_id__in=existing_ids)[:limit]

    new_ids = [str(q._id) for q in questions]
    if new_ids:
        bank.questions.extend(new_ids)
        bank.save()
    
    serializer = QuestionBankSerializer(bank)
    return Response({
        'success': True,
        'message': f'{len(new_ids)} questions added',
        'data': {
            'added': len(new_ids),
            'bank': serializer.data
        }
    })


@api_view(['POST'])
@permission_classes([IsAdmin])
def question_bank_clear_all_questions(request, pk):
    """Remove all questions from bank"""
    try:
        try:
            if len(str(pk)) == 24:
                obj_id = ObjectId(pk)
                bank = QuestionBank.objects.get(_id=obj_id)
            else:
                bank = QuestionBank.objects.get(_id=pk)
        except InvalidId:
            bank = QuestionBank.objects.get(_id=pk)
            
    except QuestionBank.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Question bank not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    removed_count = len(bank.questions or [])
    bank.questions = []
    bank.save()
    
    serializer = QuestionBankSerializer(bank)
    return Response({
        'success': True,
        'message': f'All {removed_count} questions removed',
        'data': {
            'removed': removed_count,
            'bank': serializer.data
        }
    })