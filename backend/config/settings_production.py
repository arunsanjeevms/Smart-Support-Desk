"""
Production settings used by the Docker image (DJANGO_SETTINGS_MODULE=config.settings_production).

Everything from ``settings`` still applies. This module only adds what the app
needs when it runs behind Nginx (and Cloudflare) on HTTPS, and refuses to start
with development defaults.
"""

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403
from .settings import SECRET_KEY, env_bool, env_list

DEBUG = env_bool("DJANGO_DEBUG", False)

if not SECRET_KEY or SECRET_KEY.startswith("dev-only"):
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY to a long random value in production.")

# The Angular app is served from the same domain, so the dev-only CORS regex is never needed.
CORS_ALLOWED_ORIGIN_REGEXES = []

# Nginx terminates TLS and forwards the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# HSTS is sent by Nginx for the whole site.
