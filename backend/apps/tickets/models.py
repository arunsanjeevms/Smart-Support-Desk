from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue

from .constants import ActivityType, TicketStatus


class Ticket(TimeStampedModel):
    """A support request raised by a Requester and handled by the support team."""

    reference = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.ForeignKey(
        LookupValue,
        on_delete=models.PROTECT,
        related_name="category_tickets",
        limit_choices_to={"lookup_type__code": LookupTypeCode.TICKET_CATEGORY},
    )
    priority = models.ForeignKey(
        LookupValue,
        on_delete=models.PROTECT,
        related_name="priority_tickets",
        limit_choices_to={"lookup_type__code": LookupTypeCode.TICKET_PRIORITY},
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN, db_index=True
    )
    resolution_note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_created"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_assigned",
        null=True,
        blank=True,
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_resolved",
        null=True,
        blank=True,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="ticket_status_created_idx"),
            models.Index(fields=["created_by", "-created_at"], name="ticket_owner_created_idx"),
        ]

    def __str__(self):
        return f"{self.reference} - {self.title}"

    @property
    def is_resolved(self) -> bool:
        return self.status == TicketStatus.RESOLVED


class TicketActivity(models.Model):
    """
    Append-only history of everything that happened to a ticket.

    Stored in its own collection so the audit log can be searched, sorted and
    exported across all tickets.
    """

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ticket_activities"
    )
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices, db_index=True)
    message = models.CharField(max_length=255)
    from_status = models.CharField(max_length=20, choices=TicketStatus.choices, blank=True)
    to_status = models.CharField(max_length=20, choices=TicketStatus.choices, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "ticket activities"

    def __str__(self):
        return f"{self.ticket.reference}: {self.message}"
