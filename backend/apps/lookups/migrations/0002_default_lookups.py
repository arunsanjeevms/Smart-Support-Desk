"""
Seed the configurable lists the application needs on first start.

These are ordinary database rows: after migrating they can be renamed,
re-ordered, deactivated or extended from the Django admin or the
Configuration screen.
"""

from django.db import migrations

LOOKUPS = {
    ("ticket_category", "Ticket category", "What area of the product the issue is about."): [
        # code, label, icon, color, description
        ("login_access", "Login & Access", "lock_person", "#7C3AED", "Sign-in, passwords, SSO and permissions."),
        ("billing", "Billing & Payments", "payments", "#059669", "Invoices, charges, refunds and plans."),
        ("bug", "Bug / Error", "bug_report", "#DC2626", "Something is broken or shows an error."),
        ("performance", "Performance", "speed", "#EA580C", "Slow pages, timeouts and outages."),
        ("integration", "Integrations & API", "hub", "#0891B2", "Webhooks, API keys and third-party apps."),
        ("account", "Account & Profile", "manage_accounts", "#4F46E5", "Profile, team members and settings."),
        ("data_reports", "Data & Reports", "analytics", "#0D9488", "Exports, dashboards and data accuracy."),
        ("feature_request", "Feature Request", "lightbulb", "#CA8A04", "Ideas and improvements."),
        ("other", "Other", "help", "#64748B", "Anything that does not fit above."),
    ],
    ("ticket_priority", "Ticket priority", "How urgent the issue is for the requester."): [
        ("low", "Low", "keyboard_double_arrow_down", "#64748B", "Minor inconvenience, a workaround exists."),
        ("medium", "Medium", "drag_handle", "#2563EB", "Normal priority."),
        ("high", "High", "keyboard_double_arrow_up", "#EA580C", "Important work is blocked."),
        ("critical", "Critical", "priority_high", "#DC2626", "Production down or data at risk."),
    ],
}

DEFAULTS = {"ticket_priority": "medium"}


def create_defaults(apps, schema_editor):
    LookupType = apps.get_model("lookups", "LookupType")
    LookupValue = apps.get_model("lookups", "LookupValue")
    for (code, name, description), values in LOOKUPS.items():
        lookup_type, _ = LookupType.objects.get_or_create(
            code=code, defaults={"name": name, "description": description, "is_system": True}
        )
        for order, (value_code, label, icon, color, value_description) in enumerate(values, start=1):
            LookupValue.objects.get_or_create(
                lookup_type=lookup_type,
                code=value_code,
                defaults={
                    "label": label,
                    "icon": icon,
                    "color": color,
                    "description": value_description,
                    "sort_order": order * 10,
                    "is_default": DEFAULTS.get(code) == value_code,
                },
            )


def remove_defaults(apps, schema_editor):
    LookupType = apps.get_model("lookups", "LookupType")
    LookupValue = apps.get_model("lookups", "LookupValue")
    codes = [code for code, _, _ in LOOKUPS]
    LookupValue.objects.filter(lookup_type__code__in=codes).delete()
    LookupType.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):
    dependencies = [("lookups", "0001_initial")]

    operations = [migrations.RunPython(create_defaults, remove_defaults)]
