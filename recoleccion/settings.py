"""
Django settings for recoleccion project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

config = os.environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-#covc2rqpt90ueh-$&u18u3b%wn^o)us#)7f^4k&lmfm7+=jss"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "vota-informado-recoleccion.sa-east-1.elasticbeanstalk.com",
    "177.71.161.197",
    "localhost",
    "0.0.0.0",
    "127.0.0.0",
    "127.0.0.1",
]

# CORS
# https://github.com/adamchainz/django-cors-headers
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://votainformado-staging.s3-website-sa-east-1.amazonaws.com",
]


# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_yasg",
    "corsheaders",
    "django_filters",
]

LOCAL_APPS = [
    "recoleccion.apps.RecoleccionAppConfig",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

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

ROOT_URLCONF = "recoleccion.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "recoleccion.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config.get("RDS_DB_NAME") or config.get("POSTGRES_DB"),
        "USER": config.get("RDS_USERNAME") or config.get("POSTGRES_USER"),
        "PASSWORD": config.get("RDS_PASSWORD") or config.get("POSTGRES_PASSWORD"),
        "HOST": config.get("RDS_HOSTNAME") or config.get("POSTGRES_HOST"),
        "PORT": config.get("RDS_PORT") or config.get("POSTGRES_PORT"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = "static"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
INTERNAL_MOCK_ENABLED = True

# Rest framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "recoleccion.views.paginator.StandardResultsSetPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# Logging
AXIOM_DATASET = config.get("AXIOM_DATASET", False)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"},
        "colored_formatter": {
            "()": "colorlog.ColoredFormatter",
            "format": "\n%(log_color)s%(levelname)-8s%(white)s(%(threadName)s) %(message)s",
            "log_colors": {
                "DEBUG": "bold_black",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "colored_formatter",
        },
        "axiom_handler": {
            "level": "DEBUG",
            "class": "recoleccion.utils.log_handlers.AxiomHandler",
        },
    },
    "loggers": {
        "recoleccion": {"level": "DEBUG", "handlers": ["console", "axiom_handler"], "propagate": True},
    },
}

USE_THREADS = True
