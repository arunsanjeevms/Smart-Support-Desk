"""
Load demo users and realistic tickets so the app can be explored immediately.

    python manage.py seed_demo           # add demo data (safe to run again)
    python manage.py seed_demo --reset   # wipe tickets first, then reload
"""

import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from apps.core.sequences import COUNTERS_COLLECTION
from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue
from apps.tickets import services
from apps.tickets.constants import ActivityType, TicketStatus
from apps.tickets.models import Ticket, TicketActivity

from ._demo_data import AGENTS, ADMIN, COMMENTS, REQUESTERS, TICKETS

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo users and sample tickets."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all tickets before seeding.")

    def handle(self, *args, **options):
        if options["reset"]:
            TicketActivity.objects.all().delete()
            Ticket.objects.all().delete()
            connection.database[COUNTERS_COLLECTION].delete_one({"_id": "ticket_reference"})
            self.stdout.write(self.style.WARNING("Removed existing tickets and activity."))

        users = self._create_users()
        if Ticket.objects.exists():
            self.stdout.write("Tickets already exist - skipping ticket creation (use --reset to reload).")
        else:
            self._create_tickets(users)

        self.stdout.write(self.style.SUCCESS("\nDemo data is ready. Sign in with:"))
        for account in [REQUESTERS[0], AGENTS[0], ADMIN]:
            self.stdout.write(f"  {account['role_label']:<14} {account['username']:<10} / {account['password']}")

    # ------------------------------------------------------------------
    def _create_users(self):
        created = {}
        for spec in [*REQUESTERS, *AGENTS, ADMIN]:
            user, was_created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "role": spec["role"],
                    "job_title": spec.get("job_title", ""),
                    "is_staff": spec.get("is_staff", False),
                    "is_superuser": spec.get("is_superuser", False),
                },
            )
            if was_created:
                user.set_password(spec["password"])
                user.date_joined = timezone.now() - timedelta(days=60)
                user.save()
            created[spec["username"]] = user
        self.stdout.write(f"Users ready: {len(created)}")
        return created

    def _create_tickets(self, users):
        rng = random.Random(42)  # deterministic demo data
        categories = {v.code: v for v in LookupValue.objects.of_type(LookupTypeCode.TICKET_CATEGORY)}
        priorities = {v.code: v for v in LookupValue.objects.of_type(LookupTypeCode.TICKET_PRIORITY)}
        agents = [users[a["username"]] for a in AGENTS]
        now = timezone.now()
        notify = settings.SUPPORT_DESK["EMAIL_NOTIFICATIONS"]
        settings.SUPPORT_DESK["EMAIL_NOTIFICATIONS"] = False  # no mail while seeding

        try:
            for spec in sorted(TICKETS, key=lambda t: -t["days_ago"]):
                requester = users[spec["requester"]]
                created_at = now - timedelta(days=spec["days_ago"], hours=rng.randint(0, 8), minutes=rng.randint(0, 59))
                ticket = services.create_ticket(
                    created_by=requester,
                    title=spec["title"],
                    description=spec["description"],
                    category=categories[spec["category"]],
                    priority=priorities[spec["priority"]],
                )
                Ticket.objects.filter(pk=ticket.pk).update(created_at=created_at, updated_at=created_at)
                ticket.activities.update(created_at=created_at)
                ticket.refresh_from_db()

                status = spec["status"]
                if status == TicketStatus.OPEN:
                    continue

                agent = users[spec["agent"]] if spec.get("agent") else rng.choice(agents)
                picked_up = created_at + timedelta(hours=rng.randint(1, 20))
                services.update_ticket(ticket=ticket, actor=agent, changes={"status": TicketStatus.IN_PROGRESS})
                last = picked_up

                comment = COMMENTS.get(spec["title"])
                if comment:
                    services.add_comment(ticket=ticket, author=agent, message=comment)
                    last = picked_up + timedelta(minutes=30)

                if status == TicketStatus.RESOLVED:
                    services.update_ticket(
                        ticket=ticket,
                        actor=agent,
                        changes={"status": TicketStatus.RESOLVED, "resolution_note": spec["resolution"]},
                    )
                    last = picked_up + timedelta(hours=rng.randint(2, 40))

                # Spread the history across realistic times.
                events = list(ticket.activities.exclude(activity_type=ActivityType.CREATED).order_by("created_at"))
                span = last - picked_up
                for index, event in enumerate(events):
                    offset = span * index / (len(events) - 1) if len(events) > 1 else timedelta()
                    TicketActivity.objects.filter(pk=event.pk).update(created_at=picked_up + offset)
                updates = {"updated_at": last}
                if status == TicketStatus.RESOLVED:
                    updates["resolved_at"] = last
                Ticket.objects.filter(pk=ticket.pk).update(**updates)
        finally:
            settings.SUPPORT_DESK["EMAIL_NOTIFICATIONS"] = notify

        self.stdout.write(f"Tickets created: {Ticket.objects.count()}")
