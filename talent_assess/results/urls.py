from django.urls import path
from . import views

urlpatterns = [
    path('results/summary/', views.result_summary, name='result-summary'),
    path('results/my-results/', views.result_my_results, name='result-my-results'),
    path('results/export/', views.result_export, name='result-export'),
    
    path('results/candidate/<str:candidate_id>/', views.result_by_candidate, name='result-by-candidate'),
    path('results/test/<str:test_id>/', views.result_by_test, name='result-by-test'),

    path('results/', views.result_list, name='result-list'),
    path('results/<str:pk>/', views.result_detail, name='result-detail'),  
]