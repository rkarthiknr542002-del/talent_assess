from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

schema_view = get_schema_view(
    openapi.Info(
        title="Talent Assess API",
        default_version='v1',
        description="Interview Assessment System API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@talentassess.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/auth/', include('accounts.urls')),
    path('api/questions/', include('questions.urls')),
    path('api/question-banks/', include('question_banks.urls')),
    path('api/test-templates/', include('test_templates.urls')),
    path('api/tests/', include('tests.urls')),
    path('api/results/', include('results.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/access/', include('access_management.urls')),
    
    # Swagger documentation
    # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('doc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)