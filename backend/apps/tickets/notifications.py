"""
E-mail notifications for ticket events.

Every event can be switched on or off on the Configuration screen ("Email
notifications" list) or in the Django admin. ``EMAIL_NOTIFICATIONS`` in the
settings is a master switch for all of them.

Messages are rendered straight away (so the database is only used in the
request) and then sent in a background thread, so the API is not slowed down
by the mail server.
"""

import logging
import threading

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import get_connection

from apps.core.emails import badge, build_email
from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue

from .constants import STATUS_PRESENTATION, NotificationEvent, TicketStatus

logger = logging.getLogger(__name__)
User = get_user_model()

# Reserved domains (RFC 2606/6761) can never receive mail - used by the demo accounts.
UNDELIVERABLE_SUFFIXES = (".test", ".example", ".invalid", ".localhost", ".local")
UNDELIVERABLE_DOMAINS = {"example.com", "example.org", "example.net"}


# ---------------------------------------------------------------- helpers
def is_enabled(event: str) -> bool:
    if not settings.SUPPORT_DESK["EMAIL_NOTIFICATIONS"]:
        return False
    return LookupValue.objects.filter(
        lookup_type__code=LookupTypeCode.NOTIFICATION_EVENT, code=event, is_active=True
    ).exists()


def deliverable(email: str | None) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1].lower()
    return domain not in UNDELIVERABLE_DOMAINS and not domain.endswith(UNDELIVERABLE_SUFFIXES)


def _recipients(users, exclude=None) -> list:
    seen, result = set(), []
    for user in users:
        if user is None or (exclude is not None and user.pk == exclude.pk):
            continue
        if user.pk in seen or not user.is_active or not deliverable(user.email):
            continue
        seen.add(user.pk)
        result.append(user)
    return result


def _status_badge(value: str) -> dict:
    status = TicketStatus(value)
    return badge(status.label, STATUS_PRESENTATION[status]["color"])


def _ticket_url(ticket) -> str:
    return f"{settings.SUPPORT_DESK['FRONTEND_URL']}/tickets/{ticket.pk}"


def _first_name(user) -> str:
    return user.first_name or user.username


def _short(text: str, limit: int = 600) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _send(messages) -> None:
    if not messages:
        return

    def deliver():
        try:
            get_connection(fail_silently=False).send_messages(messages)
        except Exception:  # a mail outage must never break the app
            logger.exception("Could not send %s notification e-mail(s)", len(messages))

    # The in-memory test backend is checked right after the request, so send inline there.
    if settings.EMAIL_BACKEND.endswith("locmem.EmailBackend"):
        deliver()
    else:
        threading.Thread(target=deliver, name="ticket-notifications", daemon=True).start()


def _message(user, ticket, subject, **context):
    return build_email(
        template="ticket_notification",
        subject=subject,
        to=[user.email],
        context={"ticket": ticket, "ticket_url": _ticket_url(ticket), "greeting": f"Hi {_first_name(user)},",
                 "button_label": "View ticket", **context},
    )


def _agents():
    return User.objects.filter(role=User.Role.AGENT, is_active=True)


# ---------------------------------------------------------------- events
def ticket_created(ticket) -> None:
    messages = []
    requester = ticket.created_by
    details = [
        ("Category", ticket.category.label),
        ("Priority", ticket.priority.label if ticket.priority else "Not set"),
        ("Raised by", requester.display_name),
    ]

    if is_enabled(NotificationEvent.TICKET_RECEIVED) and deliverable(requester.email):
        messages.append(_message(
            requester, ticket, f"[{ticket.reference}] We received your ticket: {ticket.title}",
            preheader=f"Your ticket {ticket.reference} is in the support queue.",
            eyebrow="Ticket received",
            heading="We've received your ticket",
            intro="Thanks for getting in touch. Your ticket is in the support queue and the team will pick it up soon.",
            status_badge=_status_badge(ticket.status),
            highlight={"label": "Your description", "text": _short(ticket.description), "tone": "teal"},
            details=details,
            closing="We'll e-mail you whenever the status changes or someone comments.",
            reason=f"You are receiving this e-mail because you raised ticket {ticket.reference}.",
        ))

    if is_enabled(NotificationEvent.NEW_TICKET_ALERT):
        for agent in _recipients(_agents(), exclude=requester):
            messages.append(_message(
                agent, ticket, f"[{ticket.reference}] New ticket: {ticket.title}",
                preheader=f"{requester.display_name} raised a new {ticket.category.label.lower()} ticket.",
                eyebrow="New ticket",
                heading=f"New ticket from {requester.display_name}",
                intro="A new ticket is waiting in the support queue.",
                status_badge=_status_badge(ticket.status),
                highlight={"label": "Description", "text": _short(ticket.description), "tone": "teal"},
                details=details,
                button_label="Open ticket",
                closing="Assign it to yourself so the requester knows someone is on it.",
                reason="You are receiving this e-mail because you are a member of the support team.",
            ))
    _send(messages)


def status_changed(ticket, actor, old_status) -> None:
    requester = ticket.created_by
    if not is_enabled(NotificationEvent.STATUS_CHANGED) or requester == actor or not deliverable(requester.email):
        return
    resolved = ticket.status == TicketStatus.RESOLVED
    new_label = TicketStatus(ticket.status).label
    _send([_message(
        requester, ticket,
        f"[{ticket.reference}] {'Resolved' if resolved else f'Now {new_label}'}: {ticket.title}",
        preheader=f"{ticket.reference} moved from {TicketStatus(old_status).label} to {new_label}.",
        eyebrow="Ticket update",
        heading="Your ticket has been resolved" if resolved else f"Your ticket is now {new_label}",
        intro=("The support team has resolved a ticket you raised. Here is what they did."
               if resolved else "There is an update on a ticket you raised."),
        old=_status_badge(old_status),
        new=_status_badge(ticket.status),
        highlight=({"label": "Resolution", "text": ticket.resolution_note, "tone": "green"}
                   if resolved and ticket.resolution_note else None),
        details=[
            ("Updated by", actor.display_name),
            ("Category", ticket.category.label),
            ("Priority", ticket.priority.label if ticket.priority else "Not set"),
            ("Assigned to", ticket.assigned_to.display_name if ticket.assigned_to else "Not assigned yet"),
        ],
        closing=("Still having trouble? Add a comment on the ticket and the support team will pick it up again."
                 if resolved else "You can follow every step and add comments on the ticket page."),
        reason=f"You are receiving this e-mail because you raised ticket {ticket.reference}.",
    )])


def ticket_assigned(ticket, actor, assignee) -> None:
    if (assignee is None or assignee == actor or not is_enabled(NotificationEvent.TICKET_ASSIGNED)
            or not deliverable(assignee.email)):
        return
    _send([_message(
        assignee, ticket, f"[{ticket.reference}] Assigned to you: {ticket.title}",
        preheader=f"{actor.display_name} assigned {ticket.reference} to you.",
        eyebrow="Assigned to you",
        heading=f"{ticket.reference} is now assigned to you",
        intro=f"{actor.display_name} assigned this ticket to you.",
        status_badge=_status_badge(ticket.status),
        highlight={"label": "Description", "text": _short(ticket.description), "tone": "teal"},
        details=[
            ("Raised by", ticket.created_by.display_name),
            ("Category", ticket.category.label),
            ("Priority", ticket.priority.label if ticket.priority else "Not set"),
        ],
        button_label="Open ticket",
        reason="You are receiving this e-mail because a ticket was assigned to you.",
    )])


def comment_added(ticket, author, comment: str, file_names: list[str] | None = None) -> None:
    if not is_enabled(NotificationEvent.COMMENT_ADDED):
        return
    requester = ticket.created_by
    if author == requester:
        # Requester wrote: tell the assigned agent, or the whole team if nobody has it yet.
        recipients = _recipients([ticket.assigned_to] if ticket.assigned_to else _agents(), exclude=author)
        heading = f"{author.display_name} commented on {ticket.reference}"
        reason = ("You are receiving this e-mail because this ticket is assigned to you."
                  if ticket.assigned_to else "You are receiving this e-mail because you are a member of the support team.")
        button = "Reply on the ticket"
    else:
        # Support team wrote: tell the requester.
        recipients = _recipients([requester], exclude=author)
        heading = f"{author.display_name} commented on your ticket"
        reason = f"You are receiving this e-mail because you raised ticket {ticket.reference}."
        button = "Reply on the ticket"

    _send([
        _message(
            user, ticket, f"[{ticket.reference}] New comment from {author.display_name}",
            preheader=_short(comment, 120),
            eyebrow="New comment",
            heading=heading,
            intro="There is a new comment on this ticket.",
            status_badge=_status_badge(ticket.status),
            highlight={"label": f"Comment from {author.display_name}", "text": _short(comment, 2000), "tone": "teal"},
            details=[
                ("Assigned to", ticket.assigned_to.display_name if ticket.assigned_to else "Not assigned yet"),
                *([("Attached files", ", ".join(file_names))] if file_names else []),
            ],
            button_label=button,
            reason=reason,
        )
        for user in recipients
    ])


def details_updated(ticket, actor, changes: list[str]) -> None:
    requester = ticket.created_by
    if (not changes or requester == actor or not is_enabled(NotificationEvent.DETAILS_UPDATED)
            or not deliverable(requester.email)):
        return
    _send([_message(
        requester, ticket, f"[{ticket.reference}] Ticket details updated: {ticket.title}",
        preheader="; ".join(changes),
        eyebrow="Ticket updated",
        heading="Your ticket details changed",
        intro=f"{actor.display_name} updated your ticket.",
        status_badge=_status_badge(ticket.status),
        highlight={"label": "What changed", "text": "\n".join(changes), "tone": "teal"},
        details=[
            ("Category", ticket.category.label),
            ("Priority", ticket.priority.label if ticket.priority else "Not set"),
        ],
        reason=f"You are receiving this e-mail because you raised ticket {ticket.reference}.",
    )])
