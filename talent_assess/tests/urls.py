from django.urls import path
from . import views

urlpatterns = [
    path('tests/', views.test_list, name='test-list'),
    path('tests/<str:pk>/', views.test_detail, name='test-detail'),
    
    path('tests/<str:pk>/start/', views.test_start, name='test-start'),
    path('tests/<str:pk>/submit/', views.test_submit, name='test-submit'),
    path('tests/<str:pk>/questions/', views.test_questions, name='test-questions'),
    path('tests/<str:pk>/save-answer/', views.test_save_answer, name='test-save-answer'),
    path('tests/<str:pk>/result/', views.test_result, name='test-result'),
    
    path('start/', views.start_test, name='start-test'),

    path('generate-ai-test/', views.generate_ai_test, name='generate-ai-test'),

    
    path('admin/test-results/', views.admin_test_results, name='admin_test_results'),
    path('admin/test-results/<str:test_id>/', views.admin_test_detail, name='admin_test_detail'),
    # path('admin/candidate/<int:candidate_id>/test-history/', views.admin_candidate_test_history, name='admin_candidate_test_history'),
    path('admin/test-statistics/', views.admin_test_statistics, name='admin_test_statistics'),
]
