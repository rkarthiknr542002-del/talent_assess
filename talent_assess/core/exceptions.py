from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """Custom exception handler for consistent error responses"""
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': response.data.get('detail', str(exc)),
                'details': response.data
            }
        }
    else:
        if isinstance(exc, ValidationError):
            response = Response({
                'success': False,
                'error': {
                    'code': 400,
                    'message': str(exc),
                    'details': {}
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(exc, NotFoundError):
            response = Response({
                'success': False,
                'error': {
                    'code': 404,
                    'message': str(exc),
                    'details': {}
                }
            }, status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, PermissionDeniedError):
            response = Response({
                'success': False,
                'error': {
                    'code': 403,
                    'message': str(exc),
                    'details': {}
                }
            }, status=status.HTTP_403_FORBIDDEN)
        elif isinstance(exc, UnauthorizedError):
            response = Response({
                'success': False,
                'error': {
                    'code': 401,
                    'message': str(exc),
                    'details': {}
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return response

class ValidationError(Exception):
    """Custom validation error"""
    pass

class NotFoundError(Exception):
    """Resource not found error"""
    pass

class PermissionDeniedError(Exception):
    """Permission denied error"""
    pass

class UnauthorizedError(Exception):
    """Unauthorized error"""
    pass