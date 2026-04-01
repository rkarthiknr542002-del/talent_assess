from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from .models import User
from bson import ObjectId

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Attempt to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise InvalidToken(_('Token contained no recognizable user identification'))
        
        try:
            user = User.objects.get(_id=user_id)
        except User.DoesNotExist:
            try:
                user = User.objects.get(_id=ObjectId(user_id))
            except:
                raise AuthenticationFailed(_('User not found'), code='user_not_found')
        except Exception:
            raise AuthenticationFailed(_('User not found'), code='user_not_found')
        
        if not user.is_active:
            raise AuthenticationFailed(_('User is inactive'), code='user_inactive')
        
        return user