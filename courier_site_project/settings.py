"""
Django Settings for Courier Site Project
Optimized for both Local Development and PythonAnywhere Deployment
Security-hardened and environment-aware
"""
import dj_database_url

from pathlib import Path
import os
import environ

# -------------------------------------------------------------------
# BASE CONFIGURATION
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ENVIRONMENT=(str, 'production')
)

# Read environment file
env_file = os.path.join(BASE_DIR, 'secrets.env.local')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
else:
    print("⚠️  Warning: secrets.env.local not found! Using defaults.")

# -------------------------------------------------------------------
# CORE SETTINGS
# -------------------------------------------------------------------
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ENVIRONMENT = env('ENVIRONMENT')  # 'development' or 'production'

# Dynamic ALLOWED_HOSTS
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
if DEBUG:
    ALLOWED_HOSTS += ['127.0.0.1', 'localhost']

# -------------------------------------------------------------------
# APPLICATIONS
# -------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'crispy_forms',
    'crispy_bootstrap5',
    'django_ratelimit',
    'axes',
    'csp',

    # Local apps
    'users.apps.UserAppConfig',
    'shipments.apps.ShipmentAppConfig',
    'delivery.apps.DeliveryAppConfig',
    'notifications.apps.NotificationsConfig',
    'payments.apps.PaymentsConfig',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',        
    }
}


RATELIMIT_USE_CACHE = 'default'

import sys
TESTING = 'test' in sys.argv

if TESTING:
    RATELIMIT_ENABLE = False  # ✅ Disable in tests
else:
    RATELIMIT_ENABLE = True


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# -------------------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',
    'csp.middleware.CSPMiddleware'
]

ROOT_URLCONF = 'courier_site_project.urls'

# -------------------------------------------------------------------
# TEMPLATES
# -------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processor.notifications_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'courier_site_project.wsgi.application'

# -------------------------------------------------------------------
# DATABASE
# -------------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    conn_max_age=600,
    ssl_require=False,
    )
}

# Connection pooling for production
if ENVIRONMENT == 'production':
    DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutes
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
    }

# -------------------------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]



# -------------------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# STATIC & MEDIA FILES
# -------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

if ENVIRONMENT == 'production':
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
else:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / 'media'

# -------------------------------------------------------------------
# EMAIL CONFIGURATION
# -------------------------------------------------------------------
if DEBUG:
    # Local development - print to console
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # Production - use SMTP
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
    EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
    DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
    EMAIL_TIMEOUT = 10

# -------------------------------------------------------------------
# SITE & PAYMENT SETTINGS
# -------------------------------------------------------------------
SITE_URL = env('SITE_URL', default='http://127.0.0.1:8000')

FLW_PUBLIC_KEY = env("FLW_PUBLIC_KEY")
FLW_SECRET_KEY = env("FLW_SECRET_KEY")
FLW_ENCRYPTION_KEY = env("FLW_ENCRYPTION_KEY")
FLW_SECRET_HASH = env("FLW_SECRET_HASH")
FLW_REDIRECT_URL = f"{SITE_URL}/payments/verify/"

# -------------------------------------------------------------------
# LOGGING CONFIGURATION
# -------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'payment_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'payments.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console' if DEBUG else 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'payments': {
            'handlers': ['payment_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------
# SESSION CONFIGURATION
# -------------------------------------------------------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_HTTPONLY = True

# -------------------------------------------------------------------
# SECURITY SETTINGS
# -------------------------------------------------------------------
if ENVIRONMENT == 'production':
    # HTTPS/SSL
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # Proxy settings (for PythonAnywhere)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # CSRF
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SAMESITE = 'Strict'
    CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
    
    # Disable debug in production
    DEBUG_PROPAGATE_EXCEPTIONS = False
    
else:
    # Development settings
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SAMESITE = 'Lax'

# -------------------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------------------
import sys
TESTING = 'test' in sys.argv

LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'users:login'

# Conditional authentication backends
if TESTING:
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',  # Only ModelBackend for tests
    ]
else:
    AUTHENTICATION_BACKENDS = [
        'axes.backends.AxesStandaloneBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]

# -------------------------------------------------------------------
# DJANGO AXES CONFIG
# -------------------------------------------------------------------
if not TESTING:
    AXES_FAILURE_LIMIT = 5
    AXES_COOLOFF_TIME = 30
    AXES_LOCKOUT_URL = '/users/lockout/'
    AXES_RESET_ON_SUCCESS = True
    AXES_ENABLED = True
    AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
    AXES_CACHE = 'default'
else:
    AXES_ENABLED = False  # Disable Axes during tests


# -------------------------------------------------------------------
# DJANGO CSP CONFIG
# -------------------------------------------------------------------
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': (
            "'self'",
            "'unsafe-inline'",
            'https://cdn.jsdelivr.net',
        ),
        'style-src': (
            "'self'",
            "'unsafe-inline'",
            'https://cdn.jsdelivr.net',
            'https://fonts.googleapis.com',
        ),
        'font-src': ("'self'", 'https://fonts.gstatic.com'),
        'img-src': ("'self'", 'data:', 'https://*'),
        'connect-src': ("'self'",),
        'frame-ancestors': ("'none'",),
        'block-all-mixed-content': True,
        # ... existing directives
        'connect-src': ("'self'", 'https://api.flutterwave.com'),  # ✅ Allow Flutterwave API
        'form-action': ("'self'", 'https://checkout.flutterwave.com'),  # ✅ Allow payment redirect
    
    }
}


# -------------------------------------------------------------------
# DJANGO SETTINGS FINALIZATION
# -------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------------------------------------------
# SECURITY CHECKS
# -------------------------------------------------------------------
if not SECRET_KEY or SECRET_KEY == 'your-secret-key-here':
    raise ValueError("🚨 SECRET_KEY must be set in secrets.env!")

if ENVIRONMENT == 'production' and DEBUG:
    raise ValueError("🚨 DEBUG must be False in production!")

if ENVIRONMENT == 'production' and not ALLOWED_HOSTS:
    raise ValueError("🚨 ALLOWED_HOSTS must be set in production!")

print(f"✅ Django loaded in {ENVIRONMENT.upper()} mode")
print(f"✅ DEBUG: {DEBUG}")
print(f"✅ SITE_URL: {SITE_URL}")


SILENCED_SYSTEM_CHECKS = ['django_ratelimit.E003', 'django_ratelimit.W001']