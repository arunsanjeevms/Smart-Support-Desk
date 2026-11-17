from django.core import mail

from apps.core.testing import ApiTestCase, category, make_user, priority
from apps.lookups.models import LookupType, LookupValue
from apps.tickets import services
from apps.tickets.constants import NotificationEvent

EVENTS_URL = "/api/lookups/values/"


def switch(event: str, enabled: bool):
    # (MongoDB cannot bulk-update through a relation, so look the list up first.)
    event_type = LookupType.objects.get(code="notification_event")
    LookupValue.objects.filter(lookup_type=event_type, code=event).update(is_active=enabled)


def sent_to(address: str):
    return [m for m in mail.outbox if address in m.to]


class NotificationTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.sam = make_user("sam", role="agent")

    def raise_ticket(self, user=None):
        return services.create_ticket(
            created_by=user or self.requester,
            title="Invoices page is blank",
            description="The invoices page shows a blank screen after it loads.",
            category=category("billing"),
            priority=priority("medium"),
        )

    # ---- new tickets ------------------------------------------------------
    def test_new_ticket_confirms_to_requester_and_alerts_the_team(self):
        self.raise_ticket()
        confirmation = sent_to("riya@acme-support.io")
        self.assertEqual(len(confirmation), 1)
        self.assertIn("We received your ticket", confirmation[0].subject)
        self.assertIn("received your ticket", confirmation[0].alternatives[0][0])
        # Both agents get the "new ticket" alert.
        self.assertEqual(len(sent_to("meera@acme-support.io")), 1)
        self.assertEqual(len(sent_to("sam@acme-support.io")), 1)
        self.assertIn("New ticket", sent_to("sam@acme-support.io")[0].subject)

    def test_switching_an_event_off_stops_that_email_only(self):
        switch(NotificationEvent.NEW_TICKET_ALERT, False)
        self.raise_ticket()
        self.assertEqual(len(sent_to("riya@acme-support.io")), 1)  # confirmation still sent
        self.assertEqual(sent_to("meera@acme-support.io"), [])
        self.assertEqual(sent_to("sam@acme-support.io"), [])

    def test_demo_addresses_that_cannot_receive_mail_are_skipped(self):
        demo = make_user("demo", email="demo.user@example.com")
        self.raise_ticket(user=demo)
        self.assertEqual(sent_to("demo.user@example.com"), [])

    # ---- updates ----------------------------------------------------------
    def test_assignment_emails_the_new_assignee_but_not_self_assignment(self):
        ticket = self.raise_ticket()
        mail.outbox.clear()
        services.update_ticket(ticket=ticket, actor=self.agent, changes={"assigned_to": self.sam})
        self.assertEqual(len(sent_to("sam@acme-support.io")), 1)
        self.assertIn("Assigned to you", sent_to("sam@acme-support.io")[0].subject)

        mail.outbox.clear()
        services.update_ticket(ticket=ticket, actor=self.agent, changes={"assigned_to": self.agent})
        self.assertEqual(sent_to("meera@acme-support.io"), [])

    def test_priority_change_tells_the_requester(self):
        ticket = self.raise_ticket()
        mail.outbox.clear()
        high = LookupValue.objects.get(lookup_type__code="ticket_priority", code="high")
        services.update_ticket(ticket=ticket, actor=self.agent, changes={"priority": high})
        message = sent_to("riya@acme-support.io")[0]
        self.assertIn("details updated", message.subject)
        self.assertIn("Priority changed from Medium to High", message.body)

    # ---- comments ---------------------------------------------------------
    def test_requester_comment_goes_to_the_assignee_or_the_whole_team(self):
        ticket = self.raise_ticket()
        mail.outbox.clear()
        services.add_comment(ticket=ticket, author=self.requester, message="Any news on this?")
        self.assertEqual(len(sent_to("meera@acme-support.io")), 1)  # unassigned: whole team
        self.assertEqual(len(sent_to("sam@acme-support.io")), 1)

        services.update_ticket(ticket=ticket, actor=self.agent, changes={"assigned_to": self.sam})
        mail.outbox.clear()
        services.add_comment(ticket=ticket, author=self.requester, message="Still broken today.")
        self.assertEqual(len(sent_to("sam@acme-support.io")), 1)  # assigned: only the assignee
        self.assertEqual(sent_to("meera@acme-support.io"), [])
        self.assertIn("Still broken today.", sent_to("sam@acme-support.io")[0].body)

    def test_agent_comment_goes_to_the_requester(self):
        ticket = self.raise_ticket()
        mail.outbox.clear()
        services.add_comment(ticket=ticket, author=self.agent, message="Could you share a screenshot?")
        message = sent_to("riya@acme-support.io")[0]
        self.assertIn("New comment from Meera", message.subject)
        self.assertIn("Could you share a screenshot?", message.alternatives[0][0])

    # ---- configuration API ------------------------------------------------
    def test_agents_switch_events_on_and_off_from_configuration(self):
        event = LookupValue.objects.get(lookup_type__code="notification_event", code="comment_added")
        response = self.client_for(self.agent).patch(f"{EVENTS_URL}{event.pk}/", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, 200)
        ticket = self.raise_ticket()
        mail.outbox.clear()
        services.add_comment(ticket=ticket, author=self.agent, message="Hello")
        self.assertEqual(mail.outbox, [])

    def test_built_in_events_cannot_be_added_renamed_in_code_or_deleted(self):
        client = self.client_for(self.agent)
        event_type = LookupType.objects.get(code="notification_event")
        event = LookupValue.objects.get(lookup_type=event_type, code="status_changed")

        response = client.post(EVENTS_URL, {"lookup_type": str(event_type.pk), "code": "x", "label": "X"}, format="json")
        self.assertEqual(response.status_code, 400)
        response = client.patch(f"{EVENTS_URL}{event.pk}/", {"code": "other"}, format="json")
        self.assertEqual(response.status_code, 400)
        response = client.patch(f"{EVENTS_URL}{event.pk}/", {"label": "Status update"}, format="json")
        self.assertEqual(response.status_code, 200)  # renaming is fine
        response = client.delete(f"{EVENTS_URL}{event.pk}/")
        self.assertEqual(response.status_code, 409)
