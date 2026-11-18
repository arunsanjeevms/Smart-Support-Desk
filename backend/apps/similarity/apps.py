from django.apps import AppConfig


class SimilarityConfig(AppConfig):
    """Suggests resolved tickets that look like a new issue (local, open-source AI)."""

    name = "apps.similarity"
    label = "similarity"
    verbose_name = "Similar ticket suggestions"
