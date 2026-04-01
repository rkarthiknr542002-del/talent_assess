from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from bson import ObjectId
from bson.errors import InvalidId

from .models import TestTemplate
from .serializers import TestTemplateSerializer
from questions.models import Question
from core.permissions import IsAdmin


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def test_template_list(request):
    """
    GET: List all test templates (with filters and pagination)
    POST: Create new test template (Admin only) - Can also add candidate email
    """
    if request.method == 'GET':
        all_templates = list(TestTemplate.objects.all().order_by('-created_at'))
        
        # Debug: Print all templates
        print("=== ALL TEMPLATES IN DB ===")
        for t in all_templates:
            print(f"ID: {t._id}, Name: {t.name}, Tech: {t.technologies}, Type: {type(t.technologies)}")
        
        all_templates = [t for t in all_templates if t.is_active]
        
        search = request.query_params.get('search')
        if search:
            search_lower = search.lower()
            all_templates = [
                t for t in all_templates 
                if (t.name and search_lower in t.name.lower()) or 
                   (t.description and search_lower in t.description.lower())
            ]
        
        # FIXED: Better technology filter
        technology = request.query_params.get('technologies')
        if technology:
            # Split multiple technologies if comma-separated
            tech_list = technology.split(',') if ',' in technology else [technology]
            tech_list = [t.lower().strip() for t in tech_list]
            
            print(f"Filtering by technologies: {tech_list}")
            
            filtered_templates = []
            for template in all_templates:
                if not template.technologies:
                    continue
                    
                # Handle different possible formats of technologies field
                template_techs = []
                
                # Case 1: If it's a list
                if isinstance(template.technologies, list):
                    template_techs = [t.lower() for t in template.technologies]
                
                # Case 2: If it's a string like "["react"]"
                elif isinstance(template.technologies, str):
                    import json
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(template.technologies)
                        if isinstance(parsed, list):
                            template_techs = [t.lower() for t in parsed]
                    except:
                        # If not JSON, treat as comma-separated or single value
                        if template.technologies.startswith('[') and template.technologies.endswith(']'):
                            # Manual parsing for "[react]"
                            clean_str = template.technologies.strip('[]').replace('"', '').replace("'", "")
                            template_techs = [t.strip().lower() for t in clean_str.split(',')]
                        else:
                            template_techs = [template.technologies.lower()]
                
                print(f"Template {template._id} technologies parsed as: {template_techs}")
                
                # Check if any of the requested technologies match
                if any(req_tech in template_techs for req_tech in tech_list):
                    filtered_templates.append(template)
            
            all_templates = filtered_templates
            print(f"After technology filter: {len(all_templates)} templates")

        experience_level = request.query_params.get('experience_level')
        if experience_level:
            all_templates = [
                t for t in all_templates 
                if t.experience_level and t.experience_level.lower() == experience_level.lower()
            ]
            print(f"After experience filter: {len(all_templates)} templates")

        # Email filter
        email = request.query_params.get('email')
        if email:
            print(f"Filtering by candidate email: {email}")
            context = {'request': request, 'email': email}
        else:
            context = {'request': request}

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        total = len(all_templates)
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_templates = all_templates[start:end]
        
        serializer = TestTemplateSerializer(paginated_templates, many=True, context=context)
        
        return Response({
            'success': True,
            'data': {
                'count': total,
                'total_pages': (total + page_size - 1) // page_size if total > 0 else 0,
                'current_page': page,
                'page_size': page_size,
                'has_next': end < total,
                'has_previous': page > 1,
                'results': serializer.data
            }
        })
    
    # POST method
    elif request.method == 'POST':
        if not request.user.is_staff:
            return Response({
                'success': False,
                'message': 'Admin permission required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Accept both field names
        candidate_email = request.data.get('candidate_email') or request.data.get('candidate_by_email')
        
        serializer = TestTemplateSerializer(data=request.data)
        if serializer.is_valid():
            # Save test template
            test_template = serializer.save(created_by=request.user)
            
            # Prepare response data
            response_data = serializer.data
            
            # If candidate email provided, fetch and add candidate details
            if candidate_email:
                try:
                    from .models import User
                    candidate = User.objects.get(email=candidate_email, role='candidate', is_active=True)
                    
                    from .serializers import UserSerializer
                    candidate_serializer = UserSerializer(candidate)
                    
                    response_data['added_candidate'] = candidate_serializer.data
                    response_data['message'] = f'Test template created and candidate {candidate_email} added successfully'
                    
                except User.DoesNotExist:
                    response_data['candidate_error'] = f'Candidate not found with email: {candidate_email}'
                except Exception as e:
                    response_data['candidate_error'] = str(e)
            
            return Response({
                'success': True,
                'message': 'Test template created successfully',
                'data': response_data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Add this fallback return (though it should never reach here)
    return Response({
        'success': False,
        'message': 'Method not allowed'
    }, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def test_template_detail(request, pk):
    """
    GET: Retrieve test template
    PUT/PATCH: Update test template (Admin only)
    DELETE: Delete test template (Admin only)
    """
    try:
        all_templates = list(TestTemplate.objects.all())
        
        template = None
        for t in all_templates:
            if str(t._id) == str(pk) or str(t._id) == str(pk):
                template = t
                break
        
        if not template:
            return Response({
                'success': False,
                'message': f'Test template with ID {pk} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not template.is_active:
            return Response({
                'success': False,
                'message': 'Test template is inactive'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'GET':
        serializer = TestTemplateSerializer(template)
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
        serializer = TestTemplateSerializer(template, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Test template updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'PATCH':
        serializer = TestTemplateSerializer(template, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Test template updated successfully',
                'data': serializer.data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        template.is_active = False
        template.save()
        return Response({
            'success': True,
            'message': 'Test template deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def test_template_validate_availability(request, pk):
    """
    Check if enough questions are available for this template
    """
    try:
        all_templates = list(TestTemplate.objects.all())
        
        template = None
        for t in all_templates:
            if str(t._id) == str(pk) or str(t._id) == str(pk):
                template = t
                break
        
        if not template:
            return Response({
                'success': False,
                'message': f'Test template with ID {pk} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not template.is_active:
            return Response({
                'success': False,
                'message': 'Test template is inactive'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    result = {}
    all_questions = list(Question.objects.all())

    print("=== DEBUG: All Questions ===")
    for q in all_questions[:5]: 
        print(f"ID: {q.id}, Category: {q.category}, Level: {q.level}, Tech: {getattr(q, 'technology', 'N/A')}")
    
    if hasattr(template, 'num_aptitude') and template.num_aptitude > 0:
        template_level = template.experience_level.lower() if template.experience_level else ""
        
        aptitude_questions = []
        for q in all_questions:
            q_category = getattr(q, 'category', '').lower() if hasattr(q, 'category') else ''
            q_level = getattr(q, 'level', '').lower() if hasattr(q, 'level') else ''
            q_is_active = getattr(q, 'is_active', True)

            if q_category == 'aptitude' and q_level == template_level and q_is_active:
                aptitude_questions.append(q)
        
        aptitude_count = len(aptitude_questions)
        
        if aptitude_count == 0:
            level_variations = {
                'mid': ['mid', 'middle', 'intermediate', 'medium'],
                'junior': ['junior', 'entry', 'beginner'],
                'senior': ['senior', 'expert', 'advanced'],
                'fresher': ['fresher', 'fresh', 'entry']
            }
            
            possible_levels = level_variations.get(template_level, [template_level])
            
            for alt_level in possible_levels:
                alt_questions = [
                    q for q in all_questions 
                    if getattr(q, 'category', '').lower() == 'aptitude'
                    and getattr(q, 'level', '').lower() == alt_level
                    and getattr(q, 'is_active', True)
                ]
                if alt_questions:
                    aptitude_questions = alt_questions
                    aptitude_count = len(alt_questions)
                    print(f"Found {aptitude_count} questions with level: {alt_level}")
                    break
        
        result['aptitude'] = {
            'required': template.num_aptitude,
            'available': aptitude_count,
            'sufficient': aptitude_count >= template.num_aptitude,
            'level_used': template.experience_level,
            'actual_count': aptitude_count
        }
    
    if hasattr(template, 'technologies') and template.technologies:
        for tech in template.technologies:
            tech_questions = [
                q for q in all_questions 
                if getattr(q, 'category', '').lower() == 'technical'
                and getattr(q, 'technology', '').lower() == tech.lower()
                and getattr(q, 'level', '').lower() == template.experience_level.lower()
                and getattr(q, 'is_active', True)
            ]
            tech_count = len(tech_questions)
            
            required_per_tech = getattr(template, 'num_technical_per_tech', 1)
            
            result[tech] = {
                'required': required_per_tech,
                'available': tech_count,
                'sufficient': tech_count >= required_per_tech
            }
    
    all_sufficient = all(v.get('sufficient', True) for v in result.values())
    
    return Response({
        'success': True,
        'data': {
            'template_id': pk,
            'template_name': getattr(template, 'name', getattr(template, 'title', 'Unknown')),
            'all_sufficient': all_sufficient,
            'details': result
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def test_template_stats(request):
    """
    Get statistics about test templates
    """
    all_templates = list(TestTemplate.objects.all())
    active_templates = [t for t in all_templates if t.is_active]
    
    total_templates = len(active_templates)
    
    by_level = {}
    for template in active_templates:
        level = template.experience_level
        if level:
            by_level[level] = by_level.get(level, 0) + 1

    by_creator = {}
    for template in active_templates:
        creator = template.created_by.email if template.created_by else 'Unknown'
        by_creator[creator] = by_creator.get(creator, 0) + 1
    
    return Response({
        'success': True,
        'data': {
            'total_templates': total_templates,
            'by_experience_level': by_level,
            'by_creator': by_creator
        }
    })


@api_view(['POST'])
@permission_classes([IsAdmin])
def test_template_bulk_create(request):
    """
    Bulk create test templates (Admin only)
    """
    templates_data = request.data.get('templates', [])
    
    if not templates_data or not isinstance(templates_data, list):
        return Response({
            'success': False,
            'message': 'templates must be a list'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    created_templates = []
    errors = []
    
    for index, template_data in enumerate(templates_data):
        serializer = TestTemplateSerializer(data=template_data)
        if serializer.is_valid():
            template = serializer.save(created_by=request.user)
            created_templates.append(serializer.data)
        else:
            errors.append({
                'index': index,
                'errors': serializer.errors
            })
    
    return Response({
        'success': len(errors) == 0,
        'message': f'{len(created_templates)} templates created, {len(errors)} failed',
        'data': {
            'created': created_templates,
            'errors': errors
        }
    })