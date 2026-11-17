from django.apps import AppConfig


class LookupsConfig(AppConfig):
    """Generic, admin-managed configuration values (categories, priorities, ...)."""

    name = "apps.lookups"
    label = "lookups"
    verbose_name = "Configuration"
