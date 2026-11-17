from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Shared building blocks: base models, serializers, exports, errors."""

    name = "apps.core"
    label = "core"
    verbose_name = "Core"
