"""
Add the "Email notifications" list: one value per notification e-mail.

Switching a value off on the Configuration screen (or in the Django admin)
stops that e-mail; renaming it only changes how it is shown.
"""

from django.db import migrations

TYPE = ("notification_event", "Email notifications", "Choose which actions send an e-mail notification.")

EVENTS = [
    # code, label, icon, colour, description
    ("ticket_received", "Ticket received", "mark_email_read", "#0F766E",
     "Confirms to the requester that their new ticket was received."),
    ("new_ticket_alert", "New ticket alert", "notification_important", "#7C3AED",
     "Tells the support team when a new ticket is raised."),
    ("ticket_assigned", "Ticket assigned", "assignment_ind", "#0891B2",
     "Tells an agent when a ticket is assigned to them by someone else."),
    ("status_changed", "Status changed", "swap_horiz", "#D97706",
     "Tells the requester when the status changes, including the resolution note."),
    ("comment_added", "New comment", "chat", "#2563EB",
     "Tells the other side about a new comment: the requester, or the assigned agent (or the team)."),
    ("details_updated", "Ticket details changed", "edit_note", "#64748B",
     "Tells the requester when the category or priority of their ticket changes."),
]


def create_events(apps, schema_editor):
    LookupType = apps.get_model("lookups", "LookupType")
    LookupValue = apps.get_model("lookups", "LookupValue")
    code, name, description = TYPE
    lookup_type, _ = LookupType.objects.get_or_create(
        code=code, defaults={"name": name, "description": description, "is_system": True}
    )
    for order, (value_code, label, icon, color, value_description) in enumerate(EVENTS, start=1):
        LookupValue.objects.get_or_create(
            lookup_type=lookup_type,
            code=value_code,
            defaults={
                "label": label,
                "icon": icon,
                "color": color,
                "description": value_description,
                "sort_order": order * 10,
                "is_active": True,
            },
        )


def remove_events(apps, schema_editor):
    LookupType = apps.get_model("lookups", "LookupType")
    LookupValue = apps.get_model("lookups", "LookupValue")
    LookupValue.objects.filter(lookup_type__code=TYPE[0]).delete()
    LookupType.objects.filter(code=TYPE[0]).delete()


class Migration(migrations.Migration):
    dependencies = [("lookups", "0002_default_lookups")]

    operations = [migrations.RunPython(create_events, remove_events)]
