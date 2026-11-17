from django.apps import AppConfig


class TicketsConfig(AppConfig):
    """Support tickets and their activity history."""

    name = "apps.tickets"
    label = "tickets"
    verbose_name = "Tickets"
