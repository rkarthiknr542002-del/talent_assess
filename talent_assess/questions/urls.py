from django.urls import path
from . import views

urlpatterns = [
    path('questions/', views.question_list, name='question-list'),
    
    path('questions/<str:pk>/', views.question_detail, name='question-detail'),
    
    path('bulk-upload/', views.bulk_upload_questions, name='bulk-upload'),
    
    path('generate-ai/', views.generate_ai_questions, name='generate-ai'),
    
    path('ai/questions/', views.get_ai_generated_questions, name='get_questions'),
    
    path('questions/<str:question_id>/', views.get_question_detail, name='question_detail'),
    
    path('test-models/', views.test_gemini_models, name='test-models'),

    path('stats/', views.question_stats, name='question-stats'),
]