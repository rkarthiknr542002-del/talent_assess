from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import random
import json
import re
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 
from .models import Question
from .serializers import QuestionSerializer, QuestionBulkUploadSerializer, QuestionStatsSerializer
from core.permissions import IsAdmin
from core.exceptions import ValidationError, NotFoundError
from core.pagination import CustomPagination
import google.genai as genai
from bson.errors import InvalidId

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by('-created_at')
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['level', 'category', 'technology', 'language', 'is_active']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_delete']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        queryset = queryset.filter(is_active=True)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(question_text__icontains=search) |
                Q(technology__icontains=search)
            )

        if self.action == 'list':
            queryset = queryset.defer('correct_answer')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create questions"""
        if not isinstance(request.data, list):
            raise ValidationError("Expected a list of questions")
        
        serializer = QuestionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            questions = []
            for item in serializer.validated_data:
                item['created_by'] = request.user
                questions.append(Question(**item))
            
            created = Question.objects.bulk_create(questions)
            return Response({
                'success': True,
                'message': f'{len(created)} questions created successfully',
                'data': QuestionSerializer(created, many=True).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """Bulk delete questions"""
        question_ids = request.data.get('question_ids', [])
        if not question_ids:
            raise ValidationError("question_ids is required")
        
        count = Question.objects.filter(_id__in=question_ids).delete()
        return Response({
            'success': True,
            'message': f'{count[0]} questions deleted successfully'
        })
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """Get random questions based on filters"""
        level = request.query_params.get('level')
        category = request.query_params.get('category')
        technology = request.query_params.get('technology')
        count = int(request.query_params.get('count', 10))
        
        queryset = Question.objects.filter(is_active=True)
        
        if level:
            queryset = queryset.filter(level=level)
        if category:
            queryset = queryset.filter(category=category)
        if technology:
            queryset = queryset.filter(technology=technology)

        total = queryset.count()
        if total < count:
            raise ValidationError(f"Only {total} questions available")
        
        random_ids = list(queryset.values_list('_id', flat=True))
        random.shuffle(random_ids)
        selected_ids = random_ids[:count]
        
        questions = queryset.filter(_id__in=selected_ids)
        serializer = self.get_serializer(questions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })

import pandas as pd
import csv
from io import TextIOWrapper
import json

@api_view(['POST'])
@permission_classes([IsAdmin])
def bulk_upload_questions(request):
    """Bulk upload questions from JSON, CSV, or Excel file"""
    file = request.FILES.get('file')
    if not file:
        return Response({
            'success': False,
            'error': {
                'code': 400,
                'message': 'File is required',
                'details': {}
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file_extension = file.name.split('.')[-1].lower()
    data = []
    
    def convert_correct_answer(value, options):
        """Convert any value to valid integer between 0-3"""
        # If None or empty string, default to 0
        if value is None or value == '' or (isinstance(value, str) and value.strip() == ''):
            return 0
        
        # If already integer between 0-3
        if isinstance(value, int):
            if 0 <= value <= 3:
                return value
            return 0  # out of range, default to 0
        
        # If already float
        if isinstance(value, float):
            try:
                num = int(value)
                if 0 <= num <= 3:
                    return num
                return 0
            except (ValueError, TypeError):
                return 0
        
        # Try to convert string to int
        if isinstance(value, str):
            # Try direct number conversion
            try:
                num = int(value)
                if 0 <= num <= 3:
                    return num
                return 0
            except (ValueError, TypeError):
                pass
            
            # Try to match with option text (case insensitive)
            value_lower = value.strip().lower()
            for idx, opt in enumerate(options):
                if opt and opt.lower() == value_lower:
                    return idx
            
            # Try common text patterns
            text_map = {
                'first': 0, '1st': 0, 'one': 0,
                'second': 1, '2nd': 1, 'two': 1,
                'third': 2, '3rd': 2, 'three': 2,
                'fourth': 3, '4th': 3, 'four': 3,
                'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
                'a': 0, 'b': 1, 'c': 2, 'd': 3,
                'option1': 0, 'option2': 1, 'option3': 2, 'option4': 3
            }
            
            if value_lower in text_map:
                result = text_map[value_lower]
                return result if result <= 3 else 0
        
        # Default fallback
        return 0
    
    try:
        # ==================== JSON FILE HANDLING ====================
        if file_extension == 'json':
            # Read JSON file
            json_data = json.loads(file.read())
            
            # Handle both formats: direct array or {questions: [...]}
            if isinstance(json_data, dict) and 'questions' in json_data:
                questions_list = json_data['questions']
            elif isinstance(json_data, list):
                questions_list = json_data
            else:
                raise ValidationError("Invalid JSON format. Expected array or object with 'questions' key")
            
            # Process each question
            for idx, question_item in enumerate(questions_list):
                # Get options
                options = question_item.get('options', [])
                
                # Convert correct_answer
                if 'correct_answer' in question_item:
                    question_item['correct_answer'] = convert_correct_answer(
                        question_item['correct_answer'], 
                        options
                    )
                else:
                    question_item['correct_answer'] = 0  # Default
                
                # Convert marks
                if 'marks' in question_item:
                    try:
                        question_item['marks'] = int(question_item['marks'])
                    except (ValueError, TypeError):
                        question_item['marks'] = 1
                else:
                    question_item['marks'] = 1
                
                # Ensure technology is null for aptitude
                if question_item.get('category') == 'aptitude':
                    question_item['technology'] = None
                
                data.append(question_item)
        
        # ==================== CSV FILE HANDLING ====================
        elif file_extension == 'csv':
            csv_file = TextIOWrapper(file, encoding='utf-8')
            csv_reader = csv.DictReader(csv_file)
            
            for row_num, row in enumerate(csv_reader, start=2):
                # Convert empty strings to None
                row = {k: (v if v != '' else None) for k, v in row.items()}
                
                # Create options array from individual option columns
                options = []
                for i in range(1, 5):
                    opt = row.get(f'option{i}')
                    if opt:
                        options.append(opt)
                    else:
                        options.append(f"Option {i}")
                row['options'] = options
                
                # Remove individual option fields
                for i in range(1, 5):
                    row.pop(f'option{i}', None)
                
                # Convert correct_answer
                if 'correct_answer' in row:
                    row['correct_answer'] = convert_correct_answer(row['correct_answer'], options)
                else:
                    row['correct_answer'] = 0
                
                # Convert marks
                if 'marks' in row and row['marks'] is not None:
                    try:
                        row['marks'] = int(row['marks'])
                    except (ValueError, TypeError):
                        row['marks'] = 1
                else:
                    row['marks'] = 1
                
                # Ensure technology is null for aptitude
                if row.get('category') == 'aptitude':
                    row['technology'] = None
                
                data.append(row)
        
        # ==================== EXCEL FILE HANDLING ====================
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file)
            
            for row_num, (_, row) in enumerate(df.iterrows(), start=2):
                row_dict = row.to_dict()
                
                # Convert NaN to None
                row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
                
                # Create options array from individual option columns
                options = []
                for i in range(1, 5):
                    opt = row_dict.get(f'option{i}')
                    if opt is not None:
                        options.append(str(opt))
                    else:
                        options.append(f"Option {i}")
                row_dict['options'] = options
                
                # Remove individual option fields
                for i in range(1, 5):
                    row_dict.pop(f'option{i}', None)
                
                # Convert correct_answer
                if 'correct_answer' in row_dict:
                    row_dict['correct_answer'] = convert_correct_answer(row_dict['correct_answer'], options)
                else:
                    row_dict['correct_answer'] = 0
                
                # Convert marks
                if 'marks' in row_dict and row_dict['marks'] is not None:
                    try:
                        row_dict['marks'] = int(row_dict['marks'])
                    except (ValueError, TypeError):
                        row_dict['marks'] = 1
                else:
                    row_dict['marks'] = 1
                
                # Ensure technology is null for aptitude
                if row_dict.get('category') == 'aptitude':
                    row_dict['technology'] = None
                
                data.append(row_dict)
        
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 400,
                    'message': f"Unsupported file format: {file_extension}. Please upload JSON, CSV, or Excel files.",
                    'details': {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ==================== SAVE USING SERIALIZER ====================
        serializer = QuestionBulkUploadSerializer(data={'questions': data}, context={'request': request})
        
        if serializer.is_valid():
            questions = serializer.save()
            return Response({
                'success': True,
                'message': f'{len(questions)} questions uploaded successfully',
                'data': QuestionSerializer(questions, many=True).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'error': {
                'code': 400,
                'message': "Invalid JSON file format",
                'details': {}
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'error': {
                'code': 400,
                'message': f"Error processing file: {str(e)}",
                'details': {}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

import google.genai as genai
import json
import time
import traceback
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from core.permissions import IsAdmin
from questions.models import Question, Technology, Category
from django.utils import timezone
from bson import ObjectId
from django.core.paginator import Paginator
from django.db.models import Q

client = genai.Client(api_key='AIzaSyB9g-EUcxLN98hY-6napQjtpjtvTkgsafw')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_ai_generated_questions(request):
    """Get all AI-generated questions with filters"""
    
    try:
        level = request.GET.get('level', '')
        category = request.GET.get('category', '')
        technology = request.GET.get('technology', '')
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        MAX_PAGE_SIZE = 500  
        if page_size > MAX_PAGE_SIZE:
            page_size = MAX_PAGE_SIZE
            
        query = Q()

        if level:
            query &= Q(level=level)
        
        if category:
            query &= Q(category=category.lower())
        
        if technology:
            query &= Q(technology=technology.lower())
        
        if search:
            query &= Q(question_text__icontains=search)
        
        questions = Question.objects.filter(query).order_by('-created_at')
        
        paginator = Paginator(questions, page_size)
        try:
            current_page = paginator.page(page)
        except:
            return Response({
                'success': False,
                'error': 'Invalid page number'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        questions_data = []
        for question in current_page:
            questions_data.append({
                'id': str(question._id),
                'level': question.level,
                'category': question.category,
                'technology': question.technology,
                'question_text': question.question_text,
                'options': question.options,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation,
                'marks': question.marks,
                'created_by': str(question.created_by._id) if question.created_by else None,
                'created_at': question.created_at,
                'is_active': question.is_active,
                'question_type': question.question_type,
                'time_to_solve_seconds': question.time_to_solve_seconds,
                'language': question.language
            })
        
        return Response({
            'success': True,
            'data': questions_data,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': current_page.has_next(),
                'has_previous': current_page.has_previous()
            }
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdmin])
def get_question_detail(request, question_id):
    """Get single question details"""
    try:
        try:
            question = Question.objects.get(_id=ObjectId(question_id))
        except:
            return Response({
                'success': False,
                'error': 'Invalid question ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = {
            'id': str(getattr(question, '_id', '')),
            'level': question.level,
            'category': question.category,
            'technology': question.technology,
            'question_text': question.question_text,
            'options': question.options,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
            'marks': question.marks,
            'created_by': str(question.created_by._id) if question.created_by else None,
            'created_at': question.created_at,
            'is_active': question.is_active,
            'question_type': question.question_type,
            'time_to_solve_seconds': question.time_to_solve_seconds,
            'language': question.language
        }
        
        return Response({
            'success': True,
            'data': data
        })
        
    except Question.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Question not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


import google.genai as genai
import json
import traceback
import time
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from core.permissions import IsAdmin
from questions.models import Question
from django.db.models import Q
from bson import ObjectId
from django.core.paginator import Paginator

client = genai.Client(api_key='AIzaSyDMgIkAy5YRZpJm4Wbf2zEKN5x5_syhY_Y')


@api_view(['GET'])
def list_gemini_models(request):
    """List all available models from Gemini API"""
    try:
        models = client.models.list()
        model_list = []
        
        for model in models:
            model_list.append({
                'name': model.name,
                'display_name': getattr(model, 'display_name', 'N/A'),
                'description': getattr(model, 'description', 'N/A')
            })
        
        return Response({
            'success': True,
            'total_models': len(model_list),
            'models': model_list
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        })


@api_view(['POST'])
@permission_classes([IsAdmin])
def generate_ai_questions(request):
    """Generate questions using Gemini"""
    
    level = request.data.get('level', 'junior')
    category = request.data.get('category', 'technical')
    technology = request.data.get('technology', 'python')
    count = int(request.data.get('count', 3))
    
    if category.lower() == 'aptitude':
        prompt = f"""Generate {count} {level} level aptitude questions.
        Return ONLY a valid JSON array. Each question must have:
        - question_text: string
        - options: array of 4 strings
        - correct_answer: integer (0-3)
        - explanation: string
        
        Example:
        [
            {{
                "question_text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": 1,
                "explanation": "2+2 equals 4"
            }}
        ]
        
        Return ONLY the JSON array, no other text.
        """
    else:
        prompt = f"""Generate {count} {level} level {technology} interview questions.
        Return ONLY a valid JSON array. Each question must have:
        - question_text: string
        - options: array of 4 strings
        - correct_answer: integer (0-3)
        - explanation: string
        
        Example:
        [
            {{
                "question_text": "What is React?",
                "options": ["Library", "Framework", "Language", "Database"],
                "correct_answer": 0,
                "explanation": "React is a JavaScript library"
            }}
        ]
        
        Return ONLY the JSON array, no other text.
        """
    
    print(f"\n=== Generating {count} {level} level {technology} questions ===")
    print(f"Prompt: {prompt[:100]}...")
    
    try:
        # Get available models first
        available_models = []
        try:
            models = client.models.list()
            for model in models:
                available_models.append(model.name)
            print(f"Available models: {available_models}")
        except:
            pass
 
        models_to_try = [
            'gemini-1.5-flash',     
            'gemini-1.5-pro',         
            'gemini-pro',              
            'models/gemini-1.5-flash', 
            'gemini-1.0-pro',          
        ]
        
        if available_models:
            models_to_try = available_models + models_to_try
        
        for model_name in models_to_try:
            try:
                print(f"\nTrying model: {model_name}")
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                
                print(f" Success with {model_name}")

                text = response.text.strip()
                print(f"Response: {text[:100]}...")

                if '[' in text and ']' in text:
                    start = text.find('[')
                    end = text.rfind(']') + 1
                    json_str = text[start:end]
                    
                    json_str = json_str.replace('\n', '').replace('\r', '')
                    json_str = ' '.join(json_str.split())
                    
                    try:
                        questions = json.loads(json_str)
                        
                        if isinstance(questions, list) and len(questions) > 0:
                            saved_count = 0
                            for q in questions[:count]:
                                try:
                                    if not all(k in q for k in ['question_text', 'options', 'correct_answer']):
                                        continue
                                    
                                    options = q.get('options', [])
                                    if not isinstance(options, list):
                                        options = ['Option A', 'Option B', 'Option C', 'Option D']
                                    while len(options) < 4:
                                        options.append(f"Option {len(options) + 1}")
                                    
                                    Question.objects.create(
                                        level=level,
                                        category=category.lower(),
                                        technology=technology.lower() if category.lower() != 'aptitude' else None,
                                        question_text=q['question_text'].strip(),
                                        options=options[:4],
                                        correct_answer=int(q.get('correct_answer', 0)),
                                        explanation=q.get('explanation', '').strip() or 'No explanation provided',
                                        marks=1,
                                        created_by=request.user if request.user.is_authenticated else None,
                                        is_active=True,
                                        question_type='multiple_choice',
                                        time_to_solve_seconds=60,
                                        language='english'
                                    )
                                    saved_count += 1
                                    
                                except Exception as e:
                                    print(f"Error saving question: {e}")
                                    continue
                            
                            return Response({
                                'success': True,
                                'message': f'Generated {saved_count} questions',
                                'model_used': model_name,
                                'data': questions[:count]
                            })
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue
                        
            except Exception as e:
                error_msg = str(e)
                print(f"Error with {model_name}: {error_msg[:100]}")
                continue
        
        return Response({
            'success': False,
            'error': 'All models failed. Please check API key and quota.',
            'help': 'Try: GET /api/questions/list-models/ to see available models'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def create_technical_prompt(level, technology, count):
    """Create prompt for technical questions"""
    
    level_descriptions = {
        'intern': 'basic fundamentals suitable for beginners. Questions should cover syntax, basic concepts, and simple usage.',
        'junior': 'core concepts, common functions, and practical applications. Include data structures, error handling, and basic patterns.',
        'mid': 'best practices, design patterns, and optimization techniques. Include architecture, performance, and advanced features.',
        'senior': 'system design, scalability, and complex scenarios. Include architecture decisions, trade-offs, and technical leadership.',
        'lead': 'expert-level concepts, strategic decisions, and team leadership. Include system architecture, technical strategy, and mentoring.'
    }
    
    description = level_descriptions.get(level, 'standard interview questions')
    
    return f"""Generate {count} UNIQUE and DIFFERENT {level} level {technology} interview questions.

IMPORTANT REQUIREMENTS:
1. Each question MUST be UNIQUE and DIFFERENT from others
2. Questions should be {description}
3. Questions must be specific to {technology}
4. ALL questions must be BRAND NEW - never seen before
5. Do NOT repeat similar questions

Return ONLY a valid JSON array with this exact structure:
[
    {{
        "question_text": "Unique question about {technology}?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "Detailed explanation why this is correct"
    }}
]

The JSON array must contain exactly {count} questions, all different from each other."""


def create_aptitude_prompt(level, count):
    """Create prompt for aptitude questions"""
    
    level_descriptions = {
        'intern': 'simple arithmetic, basic percentages, and easy logical reasoning.',
        'junior': 'moderate arithmetic, profit-loss, time-work, and logical puzzles.',
        'mid': 'complex arithmetic, data interpretation, and challenging logical reasoning.',
        'senior': 'advanced quantitative, complex puzzles, and analytical reasoning.',
        'lead': 'strategic thinking, complex data analysis, and critical reasoning.'
    }
    
    description = level_descriptions.get(level, 'standard aptitude questions')
    
    return f"""Generate {count} UNIQUE and DIFFERENT {level} level aptitude questions.

IMPORTANT REQUIREMENTS:
1. Each question MUST be UNIQUE and DIFFERENT from others
2. Questions should be {description}
3. Include mathematics, logical reasoning, and analytical questions
4. ALL questions must be BRAND NEW - never seen before
5. Do NOT repeat similar questions or patterns

Return ONLY a valid JSON array with this exact structure:
[
    {{
        "question_text": "Unique aptitude question?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "Detailed explanation why this is correct"
    }}
]

The JSON array must contain exactly {count} questions, all different from each other."""


def save_questions_to_db(questions_data, level, category_name, technology_name, user, model_used='gemini'):
    """Save AI generated questions to database"""
    saved_count = 0
    errors = []
    
    print(f"\n=== Saving {len(questions_data)} NEW {level} {technology_name} questions ===")
    
    try:
        category = category_name.lower()
        
        technology = technology_name.lower() if category_name.lower() != 'aptitude' else None
        
        for idx, q_data in enumerate(questions_data):
            try:
                existing = Question.objects.filter(
                    question_text=q_data['question_text'].strip()
                ).first()
                
                if existing:
                    print(f"Question {idx+1} duplicate, skipping...")
                    continue
                
                question = Question.objects.create(
                    level=level,
                    category=category,
                    technology=technology,
                    question_text=q_data['question_text'].strip(),
                    options=q_data.get('options', ['Option A', 'Option B', 'Option C', 'Option D']),
                    correct_answer=int(q_data.get('correct_answer', 0)),
                    explanation=q_data.get('explanation', '').strip(),
                    marks=1,
                    created_by=user if user and user.is_authenticated else None,
                    is_active=True,
                    question_type='multiple_choice',
                    time_to_solve_seconds=60,
                    language='english'
                )
                
                saved_count += 1
                print(f" Saved NEW question {idx+1}")
                
            except Exception as e:
                print(f"Error saving question {idx+1}: {str(e)}")
                errors.append(str(e))
                continue
        
        print(f"=== Saved {saved_count}/{len(questions_data)} NEW questions ===\n")
        
    except Exception as e:
        print(f"Error in save_questions_to_db: {str(e)}")
        errors.append(str(e))
    
    return saved_count


@api_view(['GET'])
def test_gemini_connection(request):
    """Test Gemini API connection"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='Return a JSON object with one key "message" containing "Hello from Gemini"'
        )
        
        return Response({
            'success': True,
            'message': 'Gemini API is working!',
            'response': response.text
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        })
    
@api_view(['GET'])
@permission_classes([IsAdmin])
def test_gemini_models(request):
    """Test different Gemini models"""
    
    genai.configure(api_key='AIzaSyBk5-_V06gCwL-B8BQ9fCBz-cIACiyiaz8')
    
    test_models = [
        'models/gemini-2.0-flash',
        'models/gemini-2.5-pro',
        'models/gemini-2.0-flash-lite',
        'models/gemini-2.5-flash',
        'models/gemini-pro-latest',
    ]
    
    results = []
    
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'working' in one word")
            results.append({
                'model': model_name,
                'status': 'working',
                'response': response.text[:50]
            })
        except Exception as e:
            results.append({
                'model': model_name,
                'status': 'failed',
                'error': str(e)
            })
    
    return Response({
        'success': True,
        'data': results
    })

@api_view(['GET'])
@permission_classes([IsAdmin])
def question_stats(request):
    """Get question statistics"""
    questions = Question.objects.all()
    serializer = QuestionStatsSerializer(questions, many=True)
    
    total = questions.count()
    by_level = {}
    by_category = {}
    by_technology = {}
    
    for level, _ in Question.LEVEL_CHOICES:
        count = questions.filter(level=level).count()
        if count > 0:
            by_level[level] = count
    
    for category, _ in Question.CATEGORY_CHOICES:
        count = questions.filter(category=category).count()
        if count > 0:
            by_category[category] = count
    
    technologies = questions.exclude(technology__isnull=True).exclude(technology='').values_list('technology', flat=True).distinct()
    for tech in technologies:
        count = questions.filter(technology=tech).count()
        by_technology[tech] = count
    
    return Response({
        'success': True,
        'data': {
            'total': total,
            'by_level': by_level,
            'by_category': by_category,
            'by_technology': by_technology,
            'details': serializer.data
        }
    })

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def question_list(request):
    """List all questions or create a new question"""
    if request.method == 'GET':
        queryset = Question.objects.all().order_by('-created_at')
        
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        technology = request.query_params.get('technology')
        if technology:
            queryset = queryset.filter(technology=technology)
        
        level = request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        paginator = Paginator(queryset, page_size)
        current_page = paginator.get_page(page)
        
        serializer = QuestionSerializer(current_page, many=True)
        
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
        
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response({
                'success': True,
                'message': 'Question created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def question_detail(request, pk):
    """
    Retrieve, update or delete a question
    """
    try:
        # Convert string ID to ObjectId
        try:
            object_id = ObjectId(pk)
        except InvalidId:
            return Response({
                'success': False,
                'message': 'Invalid question ID format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use _id field which is the actual field name in MongoDB
        question = Question.objects.get(_id=object_id)
    except Question.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Question not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = QuestionSerializer(question)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT' or request.method == 'PATCH':
        serializer = QuestionSerializer(question, data=request.data, partial=(request.method == 'PATCH'))
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Question updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        question.delete()
        return Response({
            'success': True,
            'message': 'Question deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)