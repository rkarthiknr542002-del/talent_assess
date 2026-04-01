from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('change-password/', views.change_password, name='change-password'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    
    path('token/refresh/', views.refresh_token, name='token-refresh'),
    path('token/verify/', views.verify_token, name='token-verify'),
    
    path('users/', views.UserViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-list'),
    
    path('users/search/', views.UserViewSet.as_view({'get': 'search'}), name='user-search'),
    path('users/<str:pk>/', views.UserViewSet.as_view({'get': 'retrieve', 'put': 'update','patch': 'partial_update','delete': 'destroy'}), name='user-detail'),
    
    path('users/profile/', views.UserViewSet.as_view({'get': 'profile'}), name='user-profile'),
    
    path('users/profile/update/', views.UserViewSet.as_view({'put': 'update_profile','patch': 'update_profile'}), name='user-profile-update'),
    
    # all candidates (admin only)
    path('users/candidates/', views.UserViewSet.as_view({'get': 'candidates'}), name='user-candidates'),

    path('users/<str:pk>/deactivate/', views.UserViewSet.as_view({'post': 'deactivate','delete': 'deactivate'}), name='user-deactivate'),

    path('users/email/<str:email>/', views.user_detail_by_email, name='user-detail-by-email'),
    path('users/email/<str:email>/action/', views.user_action_by_email, name='user-action-by-email'),
]