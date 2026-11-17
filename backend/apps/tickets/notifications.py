"""E-mail notifications sent to the person who raised a ticket."""

import logging

from django.conf import settings
from django.core.mail import send_mail

from .constants import TicketStatus

logger = logging.getLogger(__name__)


def status_changed(ticket, actor, old_status):
    if not settings.SUPPORT_DESK["NOTIFY_REQUESTER_ON_STATUS_CHANGE"]:
        return
    requester = ticket.created_by
    if not requester.email or requester == actor:
        return

    new_label = TicketStatus(ticket.status).label
    lines = [
        f"Hello {requester.first_name or requester.username},",
        "",
        f"Your ticket {ticket.reference} \"{ticket.title}\" moved from "
        f"{TicketStatus(old_status).label} to {new_label}.",
    ]
    if ticket.status == TicketStatus.RESOLVED and ticket.resolution_note:
        lines += ["", "Resolution note from the support team:", ticket.resolution_note]
    lines += ["", f"Updated by: {actor.display_name}", "", "Smart Support Desk"]

    try:
        send_mail(
            subject=f"[{ticket.reference}] Ticket is now {new_label}",
            message="\n".join(lines),
            from_email=None,
            recipient_list=[requester.email],
            fail_silently=False,
        )
    except Exception:  # a mail outage must never block the status update
        logger.exception("Could not send status notification for %s", ticket.reference)
