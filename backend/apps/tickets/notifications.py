"""E-mail notifications sent to the person who raised a ticket."""

import logging

from django.conf import settings

from apps.core.emails import badge, build_email

from .constants import STATUS_PRESENTATION, TicketStatus

logger = logging.getLogger(__name__)


def _status_badge(value: str) -> dict:
    status = TicketStatus(value)
    return badge(status.label, STATUS_PRESENTATION[status]["color"])


def status_changed(ticket, actor, old_status):
    if not settings.SUPPORT_DESK["NOTIFY_REQUESTER_ON_STATUS_CHANGE"]:
        return
    requester = ticket.created_by
    if not requester.email or requester == actor:
        return

    resolved = ticket.status == TicketStatus.RESOLVED
    new_label = TicketStatus(ticket.status).label
    details = [
        ("Updated by", actor.display_name),
        ("Category", ticket.category.label),
        ("Priority", ticket.priority.label if ticket.priority else "Not set"),
        ("Assigned to", ticket.assigned_to.display_name if ticket.assigned_to else "Not assigned yet"),
    ]
    message = build_email(
        template="ticket_status",
        subject=f"[{ticket.reference}] {'Resolved' if resolved else f'Now {new_label}'}: {ticket.title}",
        to=[requester.email],
        context={
            "ticket": ticket,
            "first_name": requester.first_name or requester.username,
            "old": _status_badge(old_status),
            "new": _status_badge(ticket.status),
            "resolved": resolved,
            "details": details,
            "ticket_url": f"{settings.SUPPORT_DESK['FRONTEND_URL']}/tickets/{ticket.pk}",
        },
    )
    try:
        message.send(fail_silently=False)
    except Exception:  # a mail outage must never block the status update
        logger.exception("Could not send status notification for %s", ticket.reference)
