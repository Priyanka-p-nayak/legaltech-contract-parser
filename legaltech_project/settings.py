"""
settings.py
===========
Django project settings for LegalTech.

Reads sensitive values (SECRET_KEY, DB credentials) from
environment variables via python-dotenv — never hardcoded,
never committed to git (.env is in .gitignore).

See docs/DOCKER_GUIDE.md for how these settings map onto
the docker-compose environment variables.
"""


from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
# BASE DIRECTORY
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SECURITY SETTINGS
# ============================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
DEBUG      = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# ============================================================
# INSTALLED APPLICATIONS
# ============================================================
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',        # ← NEW: Allows Member 3 dashboard

    # Our apps
    'contracts',
]

# ============================================================
# MIDDLEWARE
# CorsMiddleware MUST be before CommonMiddleware
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # ← NEW
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================
# URL CONFIGURATION
# ============================================================
ROOT_URLCONF = 'legaltech_project.urls'

# ============================================================
# TEMPLATES
# ============================================================
TEMPLATES = [
    {
        'BACKEND':  'django.template.backends.django.DjangoTemplates',
        'DIRS':     [],
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

# ============================================================
# WSGI
# ============================================================
WSGI_APPLICATION = 'legaltech_project.wsgi.application'

# ============================================================
# DATABASE — PostgreSQL
# ============================================================
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME',     'legaltech_db'),
        'USER':     os.getenv('DB_USER',     'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST':     os.getenv('DB_HOST',     'localhost'),
        'PORT':     os.getenv('DB_PORT',     '5432'),
    }
}

# ============================================================
# PASSWORD VALIDATION
# ============================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation'
            '.NumericPasswordValidator'
        ),
    },
]

# ============================================================
# INTERNATIONALISATION
# ============================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ============================================================
# STATIC FILES
# ============================================================
STATIC_URL = '/static/'

# ============================================================
# MEDIA FILES — Uploaded PDFs
# ============================================================
MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# REST FRAMEWORK CONFIGURATION
# ============================================================
REST_FRAMEWORK = {

    # Custom exception handler
    'EXCEPTION_HANDLER': (
        'legaltech_project.error_handlers'
        '.custom_exception_handler'
    ),

    # Renderers
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    # Parsers
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],

    # Pagination
    'DEFAULT_PAGINATION_CLASS': (
        'contracts.pagination.StandardPagination'
    ),
    'PAGE_SIZE': 10,

    # Date formats
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT':     '%Y-%m-%d',
}

# ============================================================
# FILE UPLOAD LIMITS — 10 MB
# ============================================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024


# ============================================================
# CORS CONFIGURATION
# Allows Member 3 dashboard to call our APIs
# from a different port or domain
# ============================================================

# In development — allow all origins
CORS_ALLOW_ALL_ORIGINS = True

# In production — replace above with specific origins:
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",      # React dev server
#     "http://localhost:5173",      # Vite dev server
#     "http://127.0.0.1:3000",
#     "http://127.0.0.1:5500",      # VS Code Live Server
#     "http://localhost:5500",
# ]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Allow these headers to be exposed to browser
CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
]

# ============================================================
# LOGGING CONFIGURATION
# Logs errors to console during development
# ============================================================
LOGGING = {
    'version':                  1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': (
                '[{levelname}] {asctime} {module} '
                '{process:d} {thread:d} {message}'
            ),
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {message}',
            'style':  '{',
        },
    },

    'handlers': {
        # Console handler — prints to terminal
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'simple',
        },

        # File handler — saves errors to file
        'file': {
            'class':     'logging.FileHandler',
            'filename':  'logs/django_errors.log',
            'formatter': 'verbose',
        },
    },

    'loggers': {
        # Django's own logger
        'django': {
            'handlers':  ['console'],
            'level':     'WARNING',
            'propagate': True,
        },

        # Our contracts app logger
        'contracts': {
            'handlers':  ['console', 'file'],
            'level':     'DEBUG',
            'propagate': False,
        },

        # Error handler logger
        'legaltech_project': {
            'handlers':  ['console', 'file'],
            'level':     'DEBUG',
            'propagate': False,
        },
    },
}

# ============================================================
# STATIC FILES — For Docker/Production
# ============================================================
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
ALLOWED_HOSTS = ['*']