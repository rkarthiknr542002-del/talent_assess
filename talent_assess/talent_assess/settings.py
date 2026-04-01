# from pathlib import Path
# from datetime import timedelta
# from decouple import config
# import os

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

# DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS = ['192.168.1.3', 'localhost', '127.0.0.1']

# # Add Gemini API Key
# GEMINI_API_KEY = config('GEMINI_API_KEY', default='your-gemini-api-key-here')

# FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')

# # Apps
# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
    
#     # Third party apps
#     'rest_framework',
#     'rest_framework_simplejwt',
#     'corsheaders',
#     'drf_yasg',
#     'drf_spectacular',
#     'django_filters',
    
#     # Local apps
#     'accounts',
#     'questions',
#     'question_banks',
#     'test_templates',
#     'tests',
#     'results',
#     'analytics',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'corsheaders.middleware.CorsMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'talent_assess.urls'


# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'talent_assess.wsgi.application'

# # MongoDB Configuration
# DATABASES = {
#     'default': {
#         'ENGINE': 'djongo',
#         'NAME': config('DB_NAME', default='quizz_db'),
#         'ENFORCE_SCHEMA': False,
#         'CLIENT': {
#             'host': config('DB_HOST', default='localhost'),
#             'port': config('DB_PORT', default=27017, cast=int),
#             'username': config('DB_USER', default=''),
#             'password': config('DB_PASSWORD', default=''),
#             'authSource': config('DB_AUTH_SOURCE', default='admin'),
#         }
#     }
# }

# # DATABASES = {
# #     'default': {
# #         'ENGINE': 'django.db.backends.sqlite3',
# #         'NAME': BASE_DIR / 'db.sqlite3',
# #     }
# # }
# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#         'OPTIONS': {
#             'min_length': 8,
#         }
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]

# # Internationalization
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'


# USE_I18N = True
# USE_TZ = True

# # Static files
# STATIC_URL = 'static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# # Media files
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# # Custom User Model
# AUTH_USER_MODEL = 'accounts.User'

# # REST Framework settings
# REST_FRAMEWORK = {
#     # 'DEFAULT_AUTHENTICATION_CLASSES': (
#     #     'accounts.authentication.CustomJWTAuthentication',     ),
    
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         'accounts.authentication.CustomJWTAuthentication',
#     ),

#     'DEFAULT_PERMISSION_CLASSES': (
#         'rest_framework.permissions.IsAuthenticated',
#     ),
#     'DEFAULT_FILTER_BACKENDS': (
#         'django_filters.rest_framework.DjangoFilterBackend',
#         'rest_framework.filters.SearchFilter',
#         'rest_framework.filters.OrderingFilter',
#     ),
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', 
#     'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPagination',
#     'PAGE_SIZE': 20,
#     'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
#     'DEFAULT_THROTTLE_CLASSES': [
#         'rest_framework.throttling.AnonRateThrottle',
#         'rest_framework.throttling.UserRateThrottle',
#     ],
#     'DEFAULT_THROTTLE_RATES': {
#         'anon': '100/day',
#         'user': '1000/day',
#     }
    
# }

# # JWT Settings
# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
#     'ROTATE_REFRESH_TOKENS': True,
#     'BLACKLIST_AFTER_ROTATION': True,
#     'UPDATE_LAST_LOGIN': True,
#     'ALGORITHM': 'HS256',
#     'SIGNING_KEY': SECRET_KEY,
#     'VERIFYING_KEY': None,
#     'AUTH_HEADER_TYPES': ('Bearer',),
#     'USER_ID_FIELD': 'id',
#     'USER_ID_CLAIM': 'user_id',
#     'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
#     'TOKEN_TYPE_CLAIM': 'token_type',
# }

# # CORS
# CORS_ALLOW_ALL_ORIGINS = True 
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:5173",
#     "http://192.168.1.4:5173",
#     "http://192.168.1.4:8000",
#     "ws://localhost:5173",  
#     "ws://192.168.1.3:5173",   
# ]

# # Email settings (for forgot password)
# EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
# EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
# EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# # Swagger settings
# # SWAGGER_SETTINGS = {
# #     'SECURITY_DEFINITIONS': {
# #         'Bearer': {
# #             'type': 'apiKey',
# #             'name': 'Authorization',
# #             'in': 'header'
# #         }
# #     },
# #     'USE_SESSION_AUTH': False,
# #     'JSON_EDITOR': True,
# #     'SUPPORTED_SUBMIT_METHODS': [
# #         'get',
# #         'post',
# #         'put',
# #         'delete',
# #         'patch'
# #     ],
# # }

# SPECTACULAR_SETTINGS = {
#     'TITLE': 'Talent Assessment API',
#     'DESCRIPTION': 'API documentation for the Talent Assessment Platform',
#     'VERSION': '1.0.0',
#     'SERVE_INCLUDE_SCHEMA': False,
    
#     # JWT authentication scheme
#     'SECURITY': [
#         {
#             'Bearer': {
#                 'type': 'http',
#                 'scheme': 'bearer',
#                 'bearerFormat': 'JWT',
#             }
#         }
#     ],
    
#     # Swagger UI settings
#     'SWAGGER_UI_SETTINGS': {
#         'deepLinking': True,
#         'persistAuthorization': True,
#         'displayRequestDuration': True,
#         'filter': True,
#         # JWT token endpoint-
#         'oauth2RedirectUrl': 'http://localhost:8000/api/docs/oauth2-redirect/',
#         'initOAuth': {
#             'clientId': 'swagger-ui',
#             'clientSecret': 'swagger-ui-secret',
#             'realm': 'swagger-ui',
#             'appName': 'Swagger UI',
#             'scopeSeparator': ' ',
#             'additionalQueryStringParams': {}
#         },
#     },
    
#     # Authentication configuration
#     'SCHEMA_PATH_PREFIX': r'/api/v1',
#     'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    
#     # Custom authentication classes
#     'APPEND_COMPONENTS': {
#         'securitySchemes': {
#             'Bearer': {
#                 'type': 'http',
#                 'scheme': 'bearer',
#                 'bearerFormat': 'JWT',
#             }
#         }
#     },
    
#     # JWT token endpoints configure 
#     'PREPROCESSING_HOOKS': [
#         'drf_spectacular.hooks.preprocess_exclude_path_format',
#     ],
# }


from pathlib import Path
from datetime import timedelta
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['192.168.1.3', 'localhost', '127.0.0.1']

# Add Gemini API Key
GEMINI_API_KEY = config('GEMINI_API_KEY', default='your-gemini-api-key-here')

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')

# Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    'drf_spectacular',
    'django_filters',
    
    # Local apps
    'accounts',
    'questions',
    'question_banks',
    'test_templates',
    'tests',
    'results',
    'analytics',
    'access_management',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'talent_assess.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'talent_assess.wsgi.application'

# MongoDB Configuration - FIXED VERSION
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': config('DB_NAME', default='quizz_db'),
        'ENFORCE_SCHEMA': False,
        'CLIENT': {
            'host': config('DB_HOST', default='mongodb://localhost:27017/'),  # Changed to full URL
            'port': config('DB_PORT', default=27017, cast=int),
            'username': config('DB_USER', default=''),
            'password': config('DB_PASSWORD', default=''),
            'authSource': config('DB_AUTH_SOURCE', default='admin'),
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'accounts.authentication.CustomJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', 
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    }
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True 
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://192.168.1.4:5173",
    "http://192.168.1.4:8000",
    "ws://localhost:5173",  
    "ws://192.168.1.3:5173",   
]

# Email settings (for forgot password)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

SPECTACULAR_SETTINGS = {
    'TITLE': 'Talent Assessment API',
    'DESCRIPTION': 'API documentation for the Talent Assessment Platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    
    # JWT authentication scheme
    'SECURITY': [
        {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    ],
    
    # Swagger UI settings
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayRequestDuration': True,
        'filter': True,
        'oauth2RedirectUrl': 'http://localhost:8000/api/docs/oauth2-redirect/',
        'initOAuth': {
            'clientId': 'swagger-ui',
            'clientSecret': 'swagger-ui-secret',
            'realm': 'swagger-ui',
            'appName': 'Swagger UI',
            'scopeSeparator': ' ',
            'additionalQueryStringParams': {}
        },
    },
    
    # Authentication configuration
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    
    # Custom authentication classes
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    
    'PREPROCESSING_HOOKS': [
        'drf_spectacular.hooks.preprocess_exclude_path_format',
    ],
}