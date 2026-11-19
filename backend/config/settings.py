"""
Django settings for the Smart Support Desk backend.

Values that change between machines (database URI, email credentials, secret
key, ...) are read from environment variables. During local development they
can be placed in ``backend/.env`` - see ``.env.example`` for every option.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-secret-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

if not DEBUG and SECRET_KEY.startswith("dev-only"):
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY to a long random value when DJANGO_DEBUG is False.")

# Production: the app runs behind Nginx (and Cloudflare) on HTTPS. Off by default for local development.
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
if env_bool("BEHIND_HTTPS_PROXY", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    # Django contrib apps re-configured to use MongoDB ObjectId primary keys
    "config.apps.MongoAdminConfig",
    "config.apps.MongoAuthConfig",
    "config.apps.MongoContentTypesConfig",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_mongodb_backend",
    # Third party
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    # Project apps
    "apps.core",
    "apps.accounts",
    "apps.lookups",
    "apps.tickets",
    "apps.similarity",
    "apps.attachments",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------
# Database - MongoDB through the official Django MongoDB Backend
# --------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django_mongodb_backend",
        # 127.0.0.1 instead of "localhost": a default MongoDB install on Windows only
        # listens on IPv4, and "localhost" can resolve to the IPv6 address ::1.
        "HOST": os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"),
        "NAME": os.getenv("MONGODB_NAME", "smart_support_desk"),
    },
}

# Every model gets a MongoDB ObjectId as its primary key.
DEFAULT_AUTO_FIELD = "django_mongodb_backend.fields.ObjectIdAutoField"

# Django's built-in apps ship migrations that use integer ids, so we keep
# MongoDB-friendly copies of them in ``mongo_migrations``.
MIGRATION_MODULES = {
    "admin": "mongo_migrations.admin",
    "auth": "mongo_migrations.auth",
    "contenttypes": "mongo_migrations.contenttypes",
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------
# Internationalisation
# --------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "apps.core.renderers.MongoJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "auth": os.getenv("AUTH_THROTTLE_RATE", "30/minute"),
        "similar": os.getenv("SIMILAR_THROTTLE_RATE", "60/minute"),
        "suggest": os.getenv("SUGGEST_THROTTLE_RATE", "120/minute"),
    },
    "DATETIME_FORMAT": "iso-8601",
}

# --------------------------------------------------------------------------
# CORS - the Angular dev server runs on a different port
# --------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200"
)
# While developing, accept the Angular app from any local address and port
# (localhost, 127.0.0.1 or [::1]), e.g. when `ng serve` picks another port.
CORS_ALLOWED_ORIGIN_REGEXES = (
    [r"^http://(localhost|127\.0\.0\.1|\[::1\]):\d+$"] if DEBUG else []
)
CORS_EXPOSE_HEADERS = ["Content-Disposition"]

# --------------------------------------------------------------------------
# Email - console backend by default, SMTP when credentials are configured
# --------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Smart Support Desk <no-reply@smartsupportdesk.local>")
EMAIL_TIMEOUT = 20

# --------------------------------------------------------------------------
# Application settings
# --------------------------------------------------------------------------
SUPPORT_DESK = {
    # Where the Angular app runs - used for links in e-mails ("View ticket").
    "FRONTEND_URL": os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/"),
    "TICKET_REFERENCE_PREFIX": os.getenv("TICKET_REFERENCE_PREFIX", "SSD"),
    "TICKET_REFERENCE_START": 1000,
    # Hard limit so an export can never pull an unbounded result set.
    "EXPORT_MAX_ROWS": int(os.getenv("EXPORT_MAX_ROWS", "5000")),
    # Master switch for notification e-mails. Individual events are switched on/off
    # in the "Email notifications" list on the Configuration screen.
    "EMAIL_NOTIFICATIONS": env_bool("EMAIL_NOTIFICATIONS", env_bool("NOTIFY_REQUESTER_ON_STATUS_CHANGE", True)),
    # Similar ticket suggestions - an open-source model that runs locally (apps/similarity).
    "SIMILARITY": {
        "ENABLED": env_bool("SIMILARITY_ENABLED", True),
        # "semantic": Sentence Transformers model (understands different wording)
        # "keyword":  TF-IDF word overlap (no model; also the automatic fallback)
        "ENGINE": os.getenv("SIMILARITY_ENGINE", "semantic"),
        "MODEL": os.getenv("SIMILARITY_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        # The brief allows up to three suggestions.
        "MAX_RESULTS": min(int(os.getenv("SIMILARITY_MAX_RESULTS", "3")), 3),
        # Cosine similarity a resolved ticket needs before it is suggested.
        "MIN_SCORE": float(os.getenv("SIMILARITY_MIN_SCORE", "0.35")),
        "KEYWORD_MIN_SCORE": float(os.getenv("SIMILARITY_KEYWORD_MIN_SCORE", "0.15")),
        # Category suggestion while typing a new ticket (calibrated on the demo data, see README).
        "CATEGORY_SUGGESTIONS": env_bool("SIMILARITY_CATEGORY_SUGGESTIONS", True),
        "CATEGORY_NEIGHBOURS": 10,
        "CATEGORY_MIN_SCORE": float(os.getenv("SIMILARITY_CATEGORY_MIN_SCORE", "0.30")),
        "CATEGORY_MIN_CONFIDENCE": float(os.getenv("SIMILARITY_CATEGORY_MIN_CONFIDENCE", "0.5")),
        "CATEGORY_DESCRIPTION_MIN_SCORE": float(os.getenv("SIMILARITY_CATEGORY_DESCRIPTION_MIN_SCORE", "0.35")),
        "CATEGORY_MAX_TICKETS": int(os.getenv("SIMILARITY_CATEGORY_MAX_TICKETS", "2000")),
        # Load the model in the background when the web server starts (first search is then instant).
        "PRELOAD": env_bool("SIMILARITY_PRELOAD", True),
    },
    # Files attached to tickets and comments (stored in MongoDB GridFS - apps/attachments).
    "ATTACHMENTS": {
        "MAX_FILE_MB": int(os.getenv("ATTACHMENT_MAX_FILE_MB", "10")),
        "MAX_FILES": int(os.getenv("ATTACHMENT_MAX_FILES", "5")),
        # Can only narrow the supported list in apps/attachments/validators.py.
        "ALLOWED_EXTENSIONS": env_list(
            "ATTACHMENT_ALLOWED_EXTENSIONS", "png,jpg,jpeg,gif,webp,pdf,txt,log,csv,json,xlsx,docx,zip"
        ),
    },
    # One-click demo sign-in on the login page. Turn off outside demos.
    "DEMO_MODE": env_bool("DEMO_MODE", True),
    "DEMO_ACCOUNTS": [
        {"username": "riya", "password": "Demo@12345", "label": "Requester",
         "description": "Raise tickets and follow their progress", "icon": "person"},
        {"username": "meera", "password": "Demo@12345", "label": "Support Agent",
         "description": "Work the queue and resolve tickets", "icon": "support_agent"},
    ],
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.db.backends": {"level": "WARNING"},
        # The similarity model's libraries are chatty at INFO level.
        "sentence_transformers": {"level": "WARNING"},
        "transformers": {"level": "WARNING"},
        "huggingface_hub": {"level": "WARNING"},
        "httpx": {"level": "WARNING"},
    },
}
