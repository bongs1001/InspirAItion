"""
Django settings for team6 project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
import environ
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

# Initialize environment variables
env = environ.Env()
environ.Env.read_env(env_file=Path(__file__).resolve().parent.parent / ".env")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-2o=o5#_qo(+_6s0@999(@x8w0jb)##okys7n4-v@6q#=!a5)h$",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "inspiraition-f2gzbvg5a3cef7ep.eastus-01.azurewebsites.net",
    "inspiraition.net",
    "www.inspiraition.net",
    "dev.inspiraition.net",
]

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://inspiraition-f2gzbvg5a3cef7ep.eastus-01.azurewebsites.net",
        "https://inspiraition.net",
        "https://www.inspiraition.net",
        "https://dev.inspiraition.net",
    ],
)


# Application definition

INSTALLED_APPS = [
    # django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party apps
    "django_bootstrap5",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap5",
    # custom apps
    "app",
    "accounts",
    "ai_playground",
    "artwork",
    "config",
    "email_app",
    "util",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "team6.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "team6.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# local sqlite3 database
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# Azure PostgreSQL database
DATABASES = {
    "default": {
        "ENGINE": env("DATABASE_ENGINE"),
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "ko-kr"

# TIME_ZONE = "UTC"
TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "https://django-app-fwgwd5amhygnhmg6.canadacentral-01.azurewebsites.net",
        "https://inspiraition-f2gzbvg5a3cef7ep.eastus-01.azurewebsites.net",
        "https://inspiraition.net",
        "https://dev.inspiraition.net",
    ],
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = True

# Azure Blob Storage settings
STORAGE_ACCOUNT_NAME = env("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = env("STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = env("CONTAINER_NAME")

AZURE_CONNECTION_STRING = (
    f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};"
    f"AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
)

DEFAULT_FILE_STORAGE = "storages.backends.azure_storage.AzureStorage"
AZURE_ACCOUNT_NAME = env("STORAGE_ACCOUNT_NAME")
AZURE_ACCOUNT_KEY = env("STORAGE_ACCOUNT_KEY")
AZURE_CONTAINER = env("CONTAINER_NAME")
AZURE_URL_EXPIRATION_SECS = 3600  # URL expiration time in seconds

MEDIA_URL = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/"

# Redirect to home URL after login (Default redirects to /accounts/profile/)
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler",
#         },
#     },
#     "loggers": {
#         "django.db.backends": {
#             "handlers": ["console"],
#             "level": "DEBUG",
#         },
#     },
# }

# Azure OpenAI (GPT-4) 설정
AZURE_OPENAI_ENDPOINT = env("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = env("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = env("AZURE_OPENAI_API_VERSION")

# Azure OpenAI (DALL-E) 설정
AZURE_DALLE_ENDPOINT = env("AZURE_DALLE_ENDPOINT")
AZURE_DALLE_API_KEY = env("AZURE_DALLE_API_KEY")
AZURE_DALLE_API_VERSION = env("AZURE_DALLE_API_VERSION")

# Azure Speech Service 설정
AZURE_SPEECH_API_KEY = env("AZURE_SPEECH_API_KEY")
AZURE_SPEECH_SERVICE_REGION = env("AZURE_SPEECH_SERVICE_REGION")

# Azure Computer Vision 설정
AZURE_COMPUTER_VISION_API_KEY = env("AZURE_COMPUTER_VISION_API_KEY")
AZURE_COMPUTER_VISION_ENDPOINT = env("AZURE_COMPUTER_VISION_ENDPOINT")


# Email settings
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
