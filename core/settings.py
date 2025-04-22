import os
import dj_database_url
from pathlib import Path
from datetime import timedelta # Asegúrate de importar timedelta
from dotenv import load_dotenv
from celery.schedules import crontab  # <-- Reemplaza la importación de django_crontab
load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-v^_mc3^kq6e)(3j=ej89sez6slzjb6_j#sy&t^wpb0%i%=xv%s'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1','web-production-0a76.up.railway.app']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    # Terceros
    'django_filters',
    'rest_framework',
    'rest_framework_simplejwt',
    'authentication.apps.AuthenticationConfig',
    'corsheaders',
    'django_celery_beat',
    'django_crontab',

    # Tus apps
    'usuarios.apps.UsuariosConfig', 
    'productos.apps.ProductosConfig', 
    'inventario.apps.InventarioConfig', 
    'ventas.apps.VentasConfig', 
    'recomendaciones',
    'pagos',  # Nueva app de pagos
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS Middleware, ¡importante!    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Ejemplo PostgreSQL (requiere psycopg2-binary y crear la base de datos 'ecommerce_db'):

#Servidor Railway
DATABASES ={
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'ecommerce_db',
#         'USER': 'postgres',
#         'PASSWORD': 'postgres',
#         'HOST': 'localhost', # O la IP/hostname de tu servidor DB
#         'PORT': '5432',      # Puerto por defecto de PostgreSQL
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



LANGUAGE_CODE = 'es-es' 
TIME_ZONE = 'America/La_Paz' 
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR,'staticfiles')


STATICFILES_STORAGE="whitenoise.storage.CompressedManifestStaticFilesStorage"
# STORAGES = {
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
# }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Configuración de Django REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # Opcional para el panel de administración
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,  # Valor recomendado (ajustable según tus necesidades)
    
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Añadir estas configuraciones adicionales recomendadas
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',  # Opcional para desarrollo
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),  # Valor predeterminado
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,  # Actualizar la fecha de último inicio de sesión
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


MEDIA_URL = '/media/'  # URL para acceder a las imágenes en el navegador
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Ruta donde se guardarán las imágenes

# --- Configuración de CORS ---
# En desarrollo, puedes permitir todo:
CORS_ALLOW_ALL_ORIGINS = True
# En producción, sé más específico:
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000", # Tu frontend React
    "http://127.0.0.1:3000",
]

CSRF_TRUSTED_ORIGINS=['http://*','https://web-production-0a76.up.railway.app']

# CORS_ALLOW_CREDENTIALS = True # Permite cookies/headers de autorización

RECOMENDACIONES_CACHE_TIMEOUT = 12 * 60 * 60  # 12 horas en segundos

CELERY_BEAT_SCHEDULE = {
    'actualizar-recomendaciones': {
        'task': 'recomendaciones.tasks.actualizar_recomendaciones',
        'schedule': crontab(hour=3, minute=0),  # Ejecutar a las 3 AM todos los días
    },
    'precalcular-recomendaciones-populares': {
        'task': 'recomendaciones.tasks.precalcular_recomendaciones_populares',
        'schedule': crontab(hour='*/4', minute=15),  # Cada 4 horas, minuto 15
    },
}

# Configuración de Stripe
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_51Q6PfFA3VhVRZlE9icPaW8KTl6aje0qhOMyJ5hxVwK6BmJeqzziM1iF6eRkO3PhttRmvdYmN8l3Qk7RB9FFbFv1c00uAf9xSsm')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_51Q6PfFA3VhVRZlE9CEO6e9DihelRFUbaGvRph3N3hQlvvvvG9ou8aCZGXpeAYWAlb9tuTj3AhJN0Dy4s6iUQu4VF00IYb7Irfe')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret_here')
STRIPE_API_VERSION = '2023-10-16'  # Usar la versión más reciente disponible

# Configurar dominio para URLs de redirección
DOMAIN_URL = os.getenv('DOMAIN_URL', 'http://localhost:3000')  # Cambiar en producción