"""
Base Django settings for the Money (FinTrack) project.
Shared by development.py and production.py.
"""

from datetime import timedelta
from pathlib import Path

import environ
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',

    # FinTrack apps
    'apps.accounts',
    'apps.transactions',
    'apps.loans',
    'apps.planning',
    'apps.budgets',
    'apps.analytics',
    'apps.notifications',
    'apps.goals',
    'apps.ai_assistant',
    'apps.reports',
    'apps.investments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Money.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Money.wsgi.application'


# Database
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=(
            f"postgresql://{env('DB_USER', default='postgres')}:"
            f"{env('DB_PASSWORD', default='')}@"
            f"{env('DB_HOST', default='localhost')}:"
            f"{env('DB_PORT', default='5432')}/"
            f"{env('DB_NAME', default='money_manage')}"
        )
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static & media files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [d for d in [BASE_DIR / 'static'] if d.exists()]
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Email
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)


# CORS / CSRF
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:5173'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['http://localhost:5173'])


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('ACCESS_TOKEN_LIFETIME', default=30)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('REFRESH_TOKEN_LIFETIME', default=7)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# Celery / Redis
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    'send-emi-reminders': {
        'task': 'apps.notifications.tasks.send_emi_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    'detect-overdue-loans': {
        'task': 'apps.notifications.tasks.detect_overdue_loans',
        'schedule': crontab(hour=1, minute=0),
    },
    'check-budget-alerts': {
        'task': 'apps.notifications.tasks.check_budget_alerts',
        'schedule': crontab(hour=9, minute=0),
    },
    'generate-recurring-transactions': {
        'task': 'apps.notifications.tasks.generate_recurring_transactions_for_all_users',
        'schedule': crontab(hour=0, minute=30),
    },
    'send-monthly-financial-summaries': {
        'task': 'apps.notifications.tasks.send_monthly_financial_summaries',
        'schedule': crontab(hour=6, minute=0, day_of_month=1),
    },
    'process-reminders': {
        'task': 'apps.notifications.tasks.process_reminders',
        'schedule': crontab(hour=7, minute=0),
    },
    'create-daily-portfolio-snapshot': {
        'task': 'apps.investments.tasks.create_daily_portfolio_snapshot',
        'schedule': crontab(hour=2, minute=0),
    },
    'remind-stale-investment-prices': {
        'task': 'apps.investments.tasks.remind_stale_investment_prices',
        'schedule': crontab(hour=8, minute=30, day_of_month=1),
    },
}


# Frontend / AI
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:5173')
AI_API_KEY = env('AI_API_KEY', default='')
AI_MODEL = env('AI_MODEL', default='')
