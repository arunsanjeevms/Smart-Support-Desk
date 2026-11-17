"""
Business rules for tickets live here rather than in views or serializers, so
they are easy to find, reuse (API, seed script, admin) and unit test.
"""

from django.conf import settings
from django.utils import timezone

from apps.core.sequences import next_sequence

from . import notifications
from .constants import ActivityType, TicketStatus
from .models import Ticket, TicketActivity


def generate_reference() -> str:
    config = settings.SUPPORT_DESK
    number = next_sequence("ticket_reference", start=config["TICKET_REFERENCE_START"])
    return f"{config['TICKET_REFERENCE_PREFIX']}-{number}"


def log_activity(ticket, actor, activity_type, message, *, from_status="", to_status="", note="", at=None):
    return TicketActivity.objects.create(
        ticket=ticket,
        actor=actor,
        activity_type=activity_type,
        message=message[:255],
        from_status=from_status,
        to_status=to_status,
        note=note,
        created_at=at or timezone.now(),
    )


def create_ticket(*, created_by, title, description, category, priority=None) -> Ticket:
    ticket = Ticket.objects.create(
        reference=generate_reference(),
        title=title.strip(),
        description=description.strip(),
        category=category,
        priority=priority,
        created_by=created_by,
    )
    log_activity(ticket, created_by, ActivityType.CREATED, f"{created_by.display_name} raised the ticket")
    return ticket


def update_ticket(*, ticket: Ticket, actor, changes: dict) -> Ticket:
    """
    Apply an agent's changes and record each of them in the activity log.

    ``changes`` may contain: status, resolution_note, assigned_to, category,
    priority. Validation (e.g. "Resolved needs a note") happens in the
    serializer before this is called.
    """
    changes = dict(changes)
    now = timezone.now()
    entries = []
    update_fields = {"updated_at"}
    old_status = ticket.status

    if "category" in changes and changes["category"] != ticket.category:
        entries.append((ActivityType.DETAILS_UPDATED,
                        f"Category changed from {ticket.category.label} to {changes['category'].label}", {}))
        ticket.category = changes["category"]
        update_fields.add("category")

    if "priority" in changes and changes["priority"] != ticket.priority:
        before = ticket.priority.label if ticket.priority else "None"
        after = changes["priority"].label if changes["priority"] else "None"
        entries.append((ActivityType.DETAILS_UPDATED, f"Priority changed from {before} to {after}", {}))
        ticket.priority = changes["priority"]
        update_fields.add("priority")

    new_status = changes.get("status", ticket.status)

    # Picking up a ticket assigns it to the agent unless someone else has it.
    if (
        "assigned_to" not in changes
        and new_status == TicketStatus.IN_PROGRESS
        and ticket.assigned_to_id is None
        and actor.is_agent
    ):
        changes["assigned_to"] = actor

    if "assigned_to" in changes and changes["assigned_to"] != ticket.assigned_to:
        assignee = changes["assigned_to"]
        message = f"Assigned to {assignee.display_name}" if assignee else "Ticket unassigned"
        entries.append((ActivityType.ASSIGNED, message, {}))
        ticket.assigned_to = assignee
        update_fields.add("assigned_to")

    note_changed = (
        "resolution_note" in changes and changes["resolution_note"].strip() != ticket.resolution_note
    )
    if note_changed:
        ticket.resolution_note = changes["resolution_note"].strip()
        update_fields.add("resolution_note")

    if new_status != old_status:
        ticket.status = new_status
        update_fields.add("status")
        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at, ticket.resolved_by = now, actor
        else:
            ticket.resolved_at, ticket.resolved_by = None, None
        update_fields |= {"resolved_at", "resolved_by"}
        entries.append((
            ActivityType.STATUS_CHANGED,
            f"Status changed from {TicketStatus(old_status).label} to {TicketStatus(new_status).label}",
            {"from_status": old_status, "to_status": new_status,
             "note": ticket.resolution_note if new_status == TicketStatus.RESOLVED else ""},
        ))
    elif note_changed:
        entries.append((ActivityType.RESOLUTION_UPDATED, "Resolution note updated",
                        {"note": ticket.resolution_note}))

    if len(update_fields) == 1:
        return ticket  # nothing changed

    ticket.save(update_fields=sorted(update_fields))
    for activity_type, message, extra in entries:
        log_activity(ticket, actor, activity_type, message, at=now, **extra)

    if new_status != old_status:
        notifications.status_changed(ticket, actor, old_status)
    return ticket


def add_comment(*, ticket: Ticket, author, message: str) -> TicketActivity:
    ticket.save(update_fields=["updated_at"])
    return log_activity(ticket, author, ActivityType.COMMENTED, f"{author.display_name} commented",
                        note=message.strip())
