"""
Load demo users and realistic tickets so the app can be explored immediately.

    python manage.py seed_demo           # add demo data (safe to run again)
    python manage.py seed_demo --reset   # wipe tickets first, then reload

    # Receive the demo accounts' notification e-mails in your own inbox
    # (riya -> you+riya@gmail.com, meera -> you+meera@gmail.com, ...):
    python manage.py seed_demo --inbox you@gmail.com

At the end the resolved tickets are encoded for the similar-ticket
suggestions (the AI model is downloaded on the first run).
"""

import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import connection
from django.utils import timezone

from apps.core.sequences import COUNTERS_COLLECTION
from apps.lookups.constants import LookupTypeCode
from apps.lookups.models import LookupValue
from apps.attachments.models import TicketAttachment
from apps.attachments.services import add_attachments
from apps.similarity.constants import SEMANTIC
from apps.similarity.engines import get_engine, similarity_settings
from apps.similarity.services import build_index
from apps.tickets import services
from apps.tickets.constants import ActivityType, TicketStatus
from apps.tickets.models import Ticket, TicketActivity

from ._demo_data import (
    ADMIN,
    AGENTS,
    COMMENTS,
    INVOICE,
    INVOICE_TICKET,
    REQUESTERS,
    TICKETS,
    WEBHOOK_LOG,
    WEBHOOK_LOG_TICKET,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Create demo users and sample tickets."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all tickets before seeding.")
        parser.add_argument(
            "--inbox",
            metavar="EMAIL",
            help="Give every demo account a plus address of this inbox (you+riya@gmail.com) so the "
            "notification e-mails actually arrive. The demo addresses on example.com cannot receive mail.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            TicketActivity.objects.all().delete()
            Ticket.objects.all().delete()
            connection.database[COUNTERS_COLLECTION].delete_one({"_id": "ticket_reference"})
            self.stdout.write(self.style.WARNING("Removed existing tickets and activity."))

        users = self._create_users()
        if options["inbox"]:
            self._route_to_inbox(users, options["inbox"])
        if Ticket.objects.exists():
            self.stdout.write("Tickets already exist - skipping ticket creation (use --reset to reload).")
        else:
            self._create_tickets(users)
            self._attach_demo_files()
        self._build_similarity_index()

        self.stdout.write(self.style.SUCCESS("\nDemo data is ready. Sign in with:"))
        for account in [REQUESTERS[0], AGENTS[0], ADMIN]:
            self.stdout.write(f"  {account['role_label']:<14} {account['username']:<10} / {account['password']}")

    # ------------------------------------------------------------------
    def _attach_demo_files(self):
        """A log file and an invoice PDF on two tickets, so attachments show up in the demo."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        samples = {
            WEBHOOK_LOG_TICKET: ("webhook-errors.log", WEBHOOK_LOG.encode(), "text/plain"),
            INVOICE_TICKET: (f"invoice-{INVOICE['number']}.pdf", _invoice_pdf(), "application/pdf"),
        }
        for title, (name, content, content_type) in samples.items():
            ticket = Ticket.objects.filter(title=title).first()
            if ticket is None:
                continue
            updated_at = ticket.updated_at
            saved = add_attachments(
                ticket=ticket, user=ticket.created_by,
                files=[SimpleUploadedFile(name, content, content_type=content_type)],
            )
            # Pretend the file came with the ticket, and keep the seeded timestamps.
            when = ticket.created_at + timedelta(minutes=2)
            TicketActivity.objects.filter(pk=saved[0].activity_id).update(created_at=when)
            TicketAttachment.objects.filter(pk__in=[item.pk for item in saved]).update(created_at=when)
            Ticket.objects.filter(pk=ticket.pk).update(updated_at=updated_at)
        self.stdout.write("Demo attachments added.")

    def _build_similarity_index(self):
        """Encode the resolved tickets now so the first similar-ticket search is instant."""
        if similarity_settings()["ENGINE"] != SEMANTIC:
            return
        engine = get_engine()
        if engine.name != SEMANTIC:
            self.stdout.write(self.style.WARNING(
                "The similarity model could not be loaded, so suggestions use keyword matching for now. "
                "Run `python manage.py build_similarity_index` once you are online."
            ))
            return
        encoded, total = build_index(engine)
        self.stdout.write(f"Similar-ticket index: {total} resolved tickets ({encoded} encoded now).")

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

    def _route_to_inbox(self, users, inbox: str):
        try:
            validate_email(inbox)
        except ValidationError:
            raise CommandError(f"'{inbox}' is not a valid e-mail address.")
        local, domain = inbox.split("@", 1)
        local = local.split("+", 1)[0]
        self.stdout.write("Demo e-mails now go to your inbox:")
        for username, user in users.items():
            user.email = f"{local}+{username}@{domain}"
            user.save(update_fields=["email"])
            self.stdout.write(f"  {username:<10} {user.email}")

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


def _invoice_pdf() -> bytes:
    """A small, realistic invoice PDF for the demo attachment."""
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Invoice {INVOICE['number']}")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(56, 780, f"Invoice {INVOICE['number']}")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(56, 756, f"Date: {INVOICE['date']}")
    pdf.drawString(56, 740, f"Billed to: {INVOICE['customer']}")
    pdf.drawString(56, 724, "GSTIN: (missing)")
    y = 690
    pdf.setFont("Helvetica-Bold", 11)
    for x, label in ((56, "Item"), (360, "Qty"), (430, "Amount")):
        pdf.drawString(x, y, label)
    pdf.setFont("Helvetica", 11)
    for item, qty, amount in INVOICE["lines"]:
        y -= 20
        pdf.drawString(56, y, item)
        pdf.drawString(360, y, qty)
        pdf.drawString(430, y, amount)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(56, y - 36, f"Total: {INVOICE['total']}")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
