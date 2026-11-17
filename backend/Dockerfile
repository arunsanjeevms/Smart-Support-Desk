# Production image for the Django API (served by gunicorn behind Nginx).
#
#   docker build -t smart-support-desk-backend ./backend
#
# Runtime configuration comes from environment variables - see
# deploy/backend.env.example for the full list.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings_production

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn==23.0.0

COPY . .

# Admin and browsable-API assets; Nginx serves them from each release folder.
RUN DJANGO_SECRET_KEY=only-used-while-building python manage.py collectstatic --no-input --verbosity 0

RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app
USER app

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", "--threads", "4", "--worker-class", "gthread", \
     "--timeout", "120", "--graceful-timeout", "20", \
     "--forwarded-allow-ips", "*", \
     "--access-logfile", "-", "--error-logfile", "-"]
