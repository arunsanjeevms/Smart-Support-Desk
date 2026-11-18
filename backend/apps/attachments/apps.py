from django.apps import AppConfig


class AttachmentsConfig(AppConfig):
    """Files (screenshots, logs, documents) attached to tickets and comments, stored in MongoDB GridFS."""

    name = "apps.attachments"
    label = "attachments"
    verbose_name = "Attachments"

    def ready(self):
        from . import signals  # noqa: F401  (removes the stored file when an attachment is deleted)
