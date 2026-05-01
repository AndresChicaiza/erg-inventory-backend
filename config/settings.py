import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from datetime import timedelta

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY    = os.getenv('SECRET_KEY', 'django-insecure-dev-only')
DEBUG         = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    # Apps propias
    'core',
    'users',
    'configuracion',      # ← NUEVA
    'productos',
    'clientes',
    'proveedores',
    'ventas',
    'compras',
    'entregas',
    'movimientos',
    'kardex',
    'reportes',
    'bodegas',
    'cxc',
    'cxp',
    'nomina',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF     = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL, conn_max_age=600, conn_health_checks=True
    )
}

AUTH_USER_MODEL = 'users.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE     = 'America/Bogota'
USE_I18N      = True
USE_TZ        = True

STATIC_URL          = '/static/'
STATIC_ROOT         = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Archivos de media (logos, imágenes) ──────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
}

CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://localhost:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ── Email — configurado en consola por ahora (sin envío real) ────────────────
# Cuando estés listo para activar Gmail, cambia esto por la config de SMTP.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Información del sistema ───────────────────────────────────────────────────
SYSTEM_NAME    = 'ERG Inventory'
SYSTEM_VERSION = '2.0'
COMPANY_NAME   = 'SUMINISTROS DACAR S.A.S.'