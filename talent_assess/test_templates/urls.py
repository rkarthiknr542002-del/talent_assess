from django.urls import path
from . import views

urlpatterns = [
    path('test-templates/', views.test_template_list, name='test-template-list'),

    path('test-templates/all/', views.test_template_list, name='test_template_detail'),
    
    path('test-templates/stats/', views.test_template_stats, name='test-template-stats'),

    path('test-templates/bulk-create/',  views.test_template_bulk_create, name='test-template-bulk-create'),

    path('test-templates/<str:pk>/', views.test_template_detail, name='test-template-detail'),
    
    path('test-templates/<str:pk>/validate-availability/', views.test_template_validate_availability, name='test-template-validate-availability'),
]