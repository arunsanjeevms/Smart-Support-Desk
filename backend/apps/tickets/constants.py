from django.db import models


class TicketStatus(models.TextChoices):
    """
    The ticket workflow. Statuses are part of the code (not the lookup tables)
    because business rules depend on them - e.g. "Resolved" needs a note.
    The UI still receives them from the API, so labels, icons and colours are
    never hard-coded in the frontend.
    """

    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"


STATUS_PRESENTATION = {
    TicketStatus.OPEN: {
        "icon": "radio_button_unchecked",
        "color": "#2563EB",
        "description": "Waiting for the support team to pick it up.",
    },
    TicketStatus.IN_PROGRESS: {
        "icon": "autorenew",
        "color": "#D97706",
        "description": "A support agent is working on it.",
    },
    TicketStatus.RESOLVED: {
        "icon": "check_circle",
        "color": "#16A34A",
        "description": "A resolution has been provided.",
    },
}

# Statuses an agent may move a ticket to from each status.
STATUS_TRANSITIONS = {
    TicketStatus.OPEN: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED],
    TicketStatus.IN_PROGRESS: [TicketStatus.OPEN, TicketStatus.RESOLVED],
    TicketStatus.RESOLVED: [TicketStatus.IN_PROGRESS, TicketStatus.OPEN],
}


class ActivityType(models.TextChoices):
    CREATED = "created", "Ticket created"
    STATUS_CHANGED = "status_changed", "Status changed"
    ASSIGNED = "assigned", "Assignment changed"
    RESOLUTION_UPDATED = "resolution_updated", "Resolution note updated"
    DETAILS_UPDATED = "details_updated", "Details updated"
    COMMENTED = "commented", "Comment added"
    ATTACHMENT_ADDED = "attachment_added", "File attached"
    ATTACHMENT_REMOVED = "attachment_removed", "File removed"


ACTIVITY_ICONS = {
    ActivityType.CREATED: "add_circle",
    ActivityType.STATUS_CHANGED: "swap_horiz",
    ActivityType.ASSIGNED: "person_add",
    ActivityType.RESOLUTION_UPDATED: "task_alt",
    ActivityType.DETAILS_UPDATED: "edit_note",
    ActivityType.COMMENTED: "chat_bubble",
    ActivityType.ATTACHMENT_ADDED: "attach_file",
    ActivityType.ATTACHMENT_REMOVED: "delete",
}


class NotificationEvent:
    """Codes of the e-mail notification events (values of the "Email notifications" list)."""

    TICKET_RECEIVED = "ticket_received"  # to the requester
    NEW_TICKET_ALERT = "new_ticket_alert"  # to the support team
    TICKET_ASSIGNED = "ticket_assigned"  # to the assigned agent
    STATUS_CHANGED = "status_changed"  # to the requester
    COMMENT_ADDED = "comment_added"  # to the other side of the conversation
    DETAILS_UPDATED = "details_updated"  # to the requester


TITLE_MIN_LENGTH = 5
TITLE_MAX_LENGTH = 150
DESCRIPTION_MIN_LENGTH = 20
DESCRIPTION_MAX_LENGTH = 5000
RESOLUTION_MIN_LENGTH = 10
