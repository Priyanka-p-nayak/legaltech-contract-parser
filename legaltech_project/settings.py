"""
settings.py
===========
Django project settings for LegalTech.

Reads sensitive values (SECRET_KEY, DB credentials) from
environment variables via python-dotenv — never hardcoded,
never committed to git (.env is in .gitignore).

See docs/DOCKER_GUIDE.md for how these settings map onto
the docker-compose environment variables.
See docs/SECURITY.md for the security decisions made here.
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

SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key-replace-in-production')

# WHY this conditional: DEBUG=True lets us get stack traces
# in development. DEBUG=False in production hides them from
# end users (security) and enables proper caching.
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# ── ALLOWED_HOSTS ─────────────────────────────────────────
# WHY not ['*'] in production: * allows DNS rebinding attacks
# where an attacker tricks your server into responding to
# requests for their malicious domain.
if DEBUG:
    # Development — allow all, for convenience
    ALLOWED_HOSTS = ['*']
else:
    # Production — only explicit hosts allowed
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        os.getenv('ALLOWED_HOST', 'localhost'),
    ]

# ============================================================
# INSTALLED APPLICATIONS
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',

    # Our apps
    'contracts',
]

# ============================================================
# MIDDLEWARE
# ORDER MATTERS — corsheaders MUST come before CommonMiddleware
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # CorsMiddleware BEFORE CommonMiddleware (required by
    # django-cors-headers documentation)
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # WHY XFrameOptionsMiddleware: prevents clickjacking attacks
    # by adding X-Frame-Options: DENY header to every response.
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
        'DIRS':     [BASE_DIR / 'templates'], 
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

        # WHY CONN_MAX_AGE: reuse DB connections across requests
        # instead of opening + closing one per request.
        # 60 seconds is a safe starting value.
        'CONN_MAX_AGE': 60,

        'OPTIONS': {
            # WHY connect_timeout: prevents a slow or unavailable
            # database from blocking Django workers indefinitely.
            'connect_timeout': 10,
        },
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
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
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

    'EXCEPTION_HANDLER': (
        'legaltech_project.error_handlers'
        '.custom_exception_handler'
    ),

    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # WHY keeping BrowsableAPIRenderer in both DEBUG modes:
        # the browsable API is a valuable development/testing tool
        # and its HTML is only served when the Accept header asks
        # for it — it doesn't leak information on JSON requests.
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],

    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],

    'DEFAULT_PAGINATION_CLASS': (
        'contracts.pagination.StandardPagination'
    ),
    'PAGE_SIZE': 10,

    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT':     '%Y-%m-%d',

    # WHY DEFAULT_THROTTLE_CLASSES commented out: throttling
    # is production-critical (prevents abuse) but we're keeping
    # it off for the internship demo to simplify testing. Add
    # before going live:
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'rest_framework.throttling.AnonRateThrottle',
    #     'rest_framework.throttling.UserRateThrottle',
    # ],
    # 'DEFAULT_THROTTLE_RATES': {
    #     'anon': '100/hour',
    #     'user': '1000/hour',
    # },
}

# ============================================================
# FILE UPLOAD LIMITS — 10 MB
# ============================================================
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ============================================================
# CORS CONFIGURATION
# ============================================================
# WHY CORS_ALLOW_ALL_ORIGINS was True before Day 30:
# It was a quick-start convenience setting added on Day 14.
# For an internship project, CORS_ALLOW_ALL_ORIGINS=True is
# acceptable in local development. BUT it's worth showing
# reviewers the correct production pattern.

if DEBUG:
    # Development: allow common local ports that Member 3
    # might be running their dashboard on.
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",      # React (Create React App)
        "http://localhost:5173",      # React (Vite)
        "http://localhost:5500",      # VS Code Live Server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500",
        "http://localhost:8080",      # Alternative dev server
    ]
else:
    # Production: ONLY the actual deployment domain.
    # Must be changed to the real domain before going live.
    CORS_ALLOWED_ORIGINS = [
        os.getenv('FRONTEND_URL', 'http://localhost:3000'),
    ]

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

CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
]

# ============================================================
# SECURITY HEADERS
# Applied via Django middleware — these headers are added to
# every HTTP response to protect against common web attacks.
# ============================================================

# WHY SECURE_BROWSER_XSS_FILTER: tells old browsers to enable
# their built-in XSS filter. Harmless in modern browsers.
SECURE_BROWSER_XSS_FILTER = True

# WHY X_FRAME_OPTIONS DENY: prevents our pages from being
# embedded in iframes on other sites (clickjacking protection).
X_FRAME_OPTIONS = 'DENY'

# WHY SECURE_CONTENT_TYPE_NOSNIFF: prevents browsers from
# "sniffing" the content type of a response — stops an attacker
# from tricking the browser into treating a PDF as executable JS.
SECURE_CONTENT_TYPE_NOSNIFF = True

# Production-only HTTPS settings (disabled in dev to avoid
# breaking local HTTP development workflow):
if not DEBUG:
    # Redirect all HTTP traffic to HTTPS
    SECURE_SSL_REDIRECT = True

    # Tell browsers to ONLY use HTTPS for this domain for 1 year
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Ensure session/CSRF cookies only travel over HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE    = True

# ============================================================
# LOGGING CONFIGURATION
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
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class':     'logging.FileHandler',
            'filename':  'logs/django_errors.log',
            'formatter': 'verbose',
        },
    },

    'loggers': {
        'django': {
            'handlers':  ['console'],
            'level':     'WARNING',
            'propagate': True,
        },
        'contracts': {
            'handlers':  ['console', 'file'],
            'level':     'DEBUG',
            'propagate': False,
        },
        'legaltech_project': {
            'handlers':  ['console', 'file'],
            'level':     'DEBUG',
            'propagate': False,
        },
    },
}