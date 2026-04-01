# access_management/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Participant URLs
    path('participants/', views.ParticipantListView.as_view(), name='participant-list'),
    path('participants/create/', views.ParticipantCreateView.as_view(), name='participant-create'),
    path('participants/<int:pk>/', views.ParticipantDetailView.as_view(), name='participant-detail'),
    path('participants/bulk-upload/', views.ParticipantBulkUploadView.as_view(), name='participant-bulk-upload'),
    
    # Test Access URLs
    path('test-access/', views.TestAccessListView.as_view(), name='test-access-list'),
    path('test-access/create/', views.TestAccessCreateView.as_view(), name='test-access-create'),
    path('test-access/<int:pk>/', views.TestAccessDetailView.as_view(), name='test-access-detail'),
    path('test-access/generate-links/', views.TestAccessGenerateLinksView.as_view(), name='generate-links'),
    # path('test-access/generate-links/', views.TestGenerateLinksView.as_view(), name='generate-links'),
    path('admin/test-links/<str:test_id>/', views.AdminTestLinksView.as_view(), name='admin-test-links'),
    path('test-access/download-links/', views.TestAccessDownloadLinksView.as_view(), name='download-links'),
    
    # Take Test URLs (Public)
    path('tests/take/<str:token>/', views.TakeTestAPIView.as_view(), name='take-test'),
    path('tests/submit/<str:token>/', views.TakeTestAPIView.as_view(), name='submit-test'),
]