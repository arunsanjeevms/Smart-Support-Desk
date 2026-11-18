from django.db.models.signals import post_delete
from django.dispatch import receiver

from . import storage
from .models import TicketAttachment


@receiver(post_delete, sender=TicketAttachment)
def remove_stored_file(sender, instance, **kwargs):
    """Deleting an attachment (or its ticket) also deletes the file in GridFS."""
    storage.delete(instance.file_id)
