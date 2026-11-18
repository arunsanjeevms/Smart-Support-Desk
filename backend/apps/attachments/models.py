from django.conf import settings
from django.db import models
from django.utils import timezone
from django_mongodb_backend.fields import ObjectIdField

from apps.tickets.models import Ticket, TicketActivity

from .validators import IMAGE_EXTENSIONS


class TicketAttachment(models.Model):
    """
    A file attached to a ticket - when it was raised, later on, or with a comment.

    Only the details live here; the bytes are stored in GridFS (``file_id``).
    ``activity`` is the timeline entry the file was added with, so the
    timeline can show each comment's files.
    """

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    activity = models.ForeignKey(
        TicketActivity, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ticket_attachments"
    )
    file_name = models.CharField(max_length=180)
    extension = models.CharField(max_length=10)
    # Decided by the server from the extension, never taken from the browser.
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField(help_text="bytes")
    file_id = ObjectIdField(help_text="GridFS id of the stored file")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.file_name} ({self.ticket_id})"

    @property
    def is_image(self) -> bool:
        return self.extension in IMAGE_EXTENSIONS
