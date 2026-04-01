from django.urls import path
from . import views

urlpatterns = [
    path('analytics/', views.analytics_list, name='analytics-list'),
    path('analytics/<str:pk>/', views.analytics_detail, name='analytics-detail'),
    
    path('summary/', views.analytics_summary, name='analytics-summary'),
    path('trends/', views.analytics_trends, name='analytics-trends'),
    
    path('dashboard/', views.dashboard_stats, name='dashboard-stats'),
    path('generate/', views.generate_analytics, name='generate-analytics'),
]