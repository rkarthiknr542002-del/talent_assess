from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'

class IsCandidate(permissions.BasePermission):
    """Allow access only to candidate users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'candidate'

class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow access only to object owner or admin"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True

        if hasattr(obj, 'candidate'):
            return obj.candidate == request.user

        if hasattr(obj, 'user'):
            return obj.user == request.user

        if hasattr(obj, 'email'):
            return obj == request.user
        
        return False

class IsOwner(permissions.BasePermission):
    """Allow access only to object owner"""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'candidate'):
            return obj.candidate == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'email'):
            return obj == request.user
        return False