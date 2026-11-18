"""
Adding and removing attachments. Every change is written to the ticket's
activity log, like any other change to a ticket.
"""

from django.utils import timezone

from apps.tickets.constants import ActivityType
from apps.tickets.services import log_activity

from . import storage
from .models import TicketAttachment
from .validators import CheckedFile, validate_files

__all__ = ["validate_files", "store", "add_attachments", "remove_attachment"]


def store(*, ticket, user, activity, checked: list[CheckedFile]) -> list[TicketAttachment]:
    """Save already-validated files to GridFS and link them to the ticket and timeline entry."""
    stored_ids = []
    try:
        for item in checked:
            stored_ids.append(storage.put(
                item.file,
                filename=item.name,
                content_type=item.content_type,
                metadata={"ticket": str(ticket.pk), "uploaded_by": str(user.pk) if user else None},
            ))
    except Exception:
        for file_id in stored_ids:  # do not leave half an upload behind
            storage.delete(file_id)
        raise

    now = timezone.now()
    return [
        TicketAttachment.objects.create(
            ticket=ticket,
            activity=activity,
            uploaded_by=user,
            file_name=item.name,
            extension=item.extension,
            content_type=item.content_type,
            size=item.size,
            file_id=file_id,
            created_at=now,
        )
        for item, file_id in zip(checked, stored_ids)
    ]


def add_attachments(*, ticket, user, files) -> list[TicketAttachment]:
    """Attach files to a ticket on their own (not with a comment)."""
    checked = validate_files(files)
    message = f"Attached {checked[0].name}" if len(checked) == 1 else f"Attached {len(checked)} files"
    ticket.save(update_fields=["updated_at"])
    entry = log_activity(ticket, user, ActivityType.ATTACHMENT_ADDED, message)
    return store(ticket=ticket, user=user, activity=entry, checked=checked)


def remove_attachment(*, attachment: TicketAttachment, user) -> None:
    ticket = attachment.ticket
    name = attachment.file_name
    attachment.delete()  # the GridFS file goes with it (signals.py)
    ticket.save(update_fields=["updated_at"])
    log_activity(ticket, user, ActivityType.ATTACHMENT_REMOVED, f"Removed {name}")
