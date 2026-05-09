"""
Django settings per al Mundial FIFA 2026.
Adaptat de l'Eurocopa 2024.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'canvia-aquesta-clau-en-produccio')

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django_registration',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'joc',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mundial2026.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'mundial2026.wsgi.application'

# --- Base de dades ---
if os.getenv('DOCKER_CONTAINER'):
    POSTGRES_HOST = 'db'
else:
    POSTGRES_HOST = '127.0.0.1'

if os.getenv('DOCKER_CONTAINER'):
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     os.getenv('PGDATABASE', 'mundial2026'),
     	    'USER':     os.getenv('PGUSER', 'postgres'),
       	    'PASSWORD': os.getenv('PGPASSWORD', 'postgres'),
       	    'HOST':     os.getenv('PGHOST', '127.0.0.1'),
            'PORT':     os.getenv('PGPORT', '5432'),
    }
}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME':   BASE_DIR / 'db.sqlite3',
        }
    }

# --- Validació de contrasenyes ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internacionalització ---
LANGUAGE_CODE = 'ca'
TIME_ZONE     = 'America/New_York'  # El Mundial 2026 es juga a USA/Canadà/Mèxic
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True

# --- Fitxers estàtics ---
STATIC_URL = '/static/'

if os.getenv('DJANGO_ENV') == 'prod':
    DEBUG         = False
ALLOWED_HOSTS = ['.disbarat.cat', '.railway.app', 'mundial2026-production-7a27.up.railway.app']  # canviar pel domini real
else:
    DEBUG         = True
    ALLOWED_HOSTS = ['mundial2026-production-7a27.up.railway.app','.railway.app']

from unipath import Path as UniPath
BASE_DIR_UNI = UniPath(__file__).ancestor(2)

STATIC_ROOT      = BASE_DIR_UNI.child("static")
STATICFILES_DIRS = (BASE_DIR_UNI.child("resources"),)
LOCALE_PATHS     = (BASE_DIR_UNI.child("languages"),)

# --- Registre d'usuaris ---
REGISTRATION_DEFAULT_FROM_EMAIL = 'El Joc del Mundial 2026 <eljocdelmunaial@gmail.com>'
ACCOUNT_ACTIVATION_DAYS = 7
LOGIN_REDIRECT_URL   = '/'
LOGIN_URL            = '/registration/login'
LOGOUT_REDIRECT_URL  = '/registration/login'
REGISTRATION_FORM    = 'joc.forms.RegistrationFormComplete'
SEND_ACTIVATION_EMAIL = False

# --- Correu electrònic ---
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_HOST_USER     = 'eljocdelmunaial@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('MUNDIAL_GMAIL_APP_PWD')
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
DEFAULT_FROM_EMAIL  = 'El Joc del Mundial 2026'

CSRF_TRUSTED_ORIGINS = ['https://*.disbarat.cat', 'https://*.127.0.0.1']

# =============================================================================
# CONSTANTS ESPECÍFIQUES DEL MUNDIAL 2026
# =============================================================================

EQUIPS_PER_GRUP = 4
NUM_GRUPS       = 12    # Grups A–L  (era 6 a l'Eurocopa)
ID_ADMIN        = 1

# Total de partits:
#   Fase de grups:  12 grups × 6 partits = 72  (partits   1–72)
#   Setzens:        16 partits                  (partits  73–88)
#   Vuitens:         8 partits                  (partits  89–96)
#   Quarts:          4 partits                  (partits  97–100)
#   Semifinals:      2 partits                  (partits 101–102)
#   Tercer/quart:    1 partit                   (partit  103)
#   Final:           1 partit                   (partit  104)
#   TOTAL:         104 partits
NUM_PARTITS       = 104   # era 51 a l'Eurocopa
NUM_PARTITS_GRUPS = 72    # era 36 a l'Eurocopa
