from django.urls import path
from . import views

urlpatterns = [
    path('question-banks/', views.question_bank_list, name='question-bank-list'),
    path('question-banks/<str:pk>/', views.question_bank_detail, name='question-bank-detail'),
    
    path('question-banks/<str:pk>/add-questions/', views.question_bank_add_questions, name='question-bank-add-questions'),
    path('question-banks/<str:pk>/remove-questions/', views.question_bank_remove_questions, name='question-bank-remove-questions'),
    path('question-banks/<str:pk>/questions/', views.question_bank_questions, name='question-bank-questions'),
    path('question-banks/<str:pk>/stats/', views.question_bank_stats, name='question-bank-stats'),
    path('question-banks/<str:pk>/bulk-add-questions/', views.question_bank_bulk_add_questions, name='question-bank-bulk-add-questions'),
    path('question-banks/<str:pk>/clear-all-questions/', views.question_bank_clear_all_questions, name='question-bank-clear-all-questions'),
]