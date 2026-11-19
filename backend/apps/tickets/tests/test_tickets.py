from django.core import mail

from apps.core.testing import ApiTestCase, User, category, make_user, priority
from apps.lookups.models import LookupValue
from apps.tickets import services
from apps.tickets.models import Ticket, TicketActivity

URL = "/api/tickets/"


def new_ticket(user, title="Cannot open the invoices page", code="billing", **extra):
    return services.create_ticket(
        created_by=user,
        title=title,
        description=extra.pop("description", "The invoices page shows a blank screen after loading."),
        category=category(code),
        priority=extra.pop("priority", priority("medium")),
    )


class CreateTicketTests(ApiTestCase):
    def payload(self, **overrides):
        data = {
            "title": "Unable to download invoices",
            "description": "Clicking the download button on any invoice does nothing at all.",
            "category": str(category("billing").pk),
        }
        data.update(overrides)
        return data

    def test_support_team_cannot_raise_tickets(self):
        admin = make_user("admin", role=User.Role.AGENT, is_staff=True, is_superuser=True)
        for user in (self.agent, admin):
            response = self.client_for(user).post(URL, self.payload(), format="json")
            self.assertEqual(response.status_code, 403)
            self.assertIn("raised by requesters", response.data["message"])
        self.assertFalse(Ticket.objects.exists())

    def test_requester_creates_ticket_with_reference_and_default_priority(self):
        response = self.client_for(self.requester).post(URL, self.payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertRegex(response.data["reference"], r"^SSD-\d{4,}$")
        self.assertEqual(response.data["status"], "open")
        self.assertEqual(response.data["priority"]["code"], "medium")
        self.assertEqual(response.data["created_by"]["username"], "ragavan")
        ticket = Ticket.objects.get(pk=response.data["id"])
        self.assertEqual(ticket.activities.get().activity_type, "created")

    def test_references_are_unique_and_sequential(self):
        first = new_ticket(self.requester)
        second = new_ticket(self.requester)
        self.assertEqual(int(second.reference.split("-")[1]), int(first.reference.split("-")[1]) + 1)

    def test_missing_fields_return_helpful_messages(self):
        response = self.client_for(self.requester).post(URL, {}, format="json")
        self.assertEqual(response.status_code, 400)
        errors = response.data["errors"]
        self.assertEqual(errors["title"], ["Please enter a title."])
        self.assertEqual(errors["description"], ["Please describe the issue."])
        self.assertEqual(errors["category"], ["Please choose a category."])

    def test_short_values_and_bad_category_are_rejected(self):
        response = self.client_for(self.requester).post(
            URL, self.payload(title="Hey", description="too short", category="not-an-id"), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data["errors"]), {"title", "description", "category"})

    def test_priority_id_cannot_be_used_as_category(self):
        response = self.client_for(self.requester).post(
            URL, self.payload(category=str(priority("high").pk)), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["category"], ["Please choose a valid category."])

    def test_inactive_category_is_rejected(self):
        LookupValue.objects.filter(pk=category("billing").pk).update(is_active=False)
        response = self.client_for(self.requester).post(URL, self.payload(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("no longer available", response.data["errors"]["category"][0])

    def test_anonymous_users_cannot_create(self):
        self.assertEqual(self.anon.post(URL, self.payload(), format="json").status_code, 401)


class ListAndDetailTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.mine = new_ticket(self.requester, "Login page keeps loading", "login_access")
        self.billing = new_ticket(self.requester, "Charged twice this month", "billing", priority=priority("high"))
        self.theirs = new_ticket(self.other_requester, "Dashboard is slow", "performance",
                                 priority=priority("critical"))
        services.update_ticket(ticket=self.theirs, actor=self.agent, changes={"status": "in_progress"})

    def refs(self, response):
        return [t["reference"] for t in response.data["results"]]

    def test_requester_only_sees_own_tickets(self):
        response = self.client_for(self.requester).get(URL)
        self.assertEqual(response.data["count"], 2)
        self.assertNotIn(self.theirs.reference, self.refs(response))

    def test_requester_cannot_open_someone_elses_ticket(self):
        response = self.client_for(self.requester).get(f"{URL}{self.theirs.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_agent_sees_everything_newest_first(self):
        response = self.client_for(self.agent).get(URL)
        self.assertEqual(self.refs(response), [self.theirs.reference, self.billing.reference, self.mine.reference])

    def test_filter_by_status_and_category(self):
        client = self.client_for(self.agent)
        self.assertEqual(self.refs(client.get(URL + "?status=in_progress")), [self.theirs.reference])
        self.assertEqual(client.get(URL + "?status=open,in_progress").data["count"], 3)
        cat = category("billing").pk
        self.assertEqual(self.refs(client.get(f"{URL}?category={cat}")), [self.billing.reference])

    def test_filter_by_assignment(self):
        client = self.client_for(self.agent)
        self.assertEqual(self.refs(client.get(URL + "?assigned_to=me")), [self.theirs.reference])
        self.assertEqual(client.get(URL + "?assigned_to=unassigned").data["count"], 2)

    def test_search_matches_title_description_and_category(self):
        client = self.client_for(self.agent)
        self.assertEqual(self.refs(client.get(URL + "?search=charged")), [self.billing.reference])
        self.assertEqual(self.refs(client.get(URL + "?search=Performance")), [self.theirs.reference])

    def test_sorting_including_related_fields(self):
        client = self.client_for(self.agent)
        by_title = self.refs(client.get(URL + "?ordering=title"))
        self.assertEqual(by_title, [self.billing.reference, self.theirs.reference, self.mine.reference])
        by_priority = self.refs(client.get(URL + "?ordering=-priority__sort_order"))
        self.assertEqual(by_priority[0], self.theirs.reference)

    def test_pagination(self):
        response = self.client_for(self.agent).get(URL + "?page_size=2&page=2")
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(response.data["total_pages"], 2)
        self.assertEqual(len(response.data["results"]), 1)

    def test_detail_tells_ui_what_the_user_may_do(self):
        agent_view = self.client_for(self.agent).get(f"{URL}{self.mine.pk}/").data
        self.assertTrue(agent_view["can_manage"])
        self.assertEqual([s["value"] for s in agent_view["allowed_statuses"]], ["in_progress", "resolved"])
        requester_view = self.client_for(self.requester).get(f"{URL}{self.mine.pk}/").data
        self.assertFalse(requester_view["can_manage"])
        self.assertEqual(requester_view["allowed_statuses"], [])

    def test_stats_are_scoped_to_the_user(self):
        agent_stats = self.client_for(self.agent).get(URL + "stats/").data
        self.assertEqual(agent_stats["total"], 3)
        counts = {s["value"]: s["count"] for s in agent_stats["by_status"]}
        self.assertEqual(counts, {"open": 2, "in_progress": 1, "resolved": 0})
        self.assertEqual(agent_stats["assigned_to_me_open"], 1)
        self.assertEqual(self.client_for(self.requester).get(URL + "stats/").data["total"], 2)


class StatusWorkflowTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.ticket = new_ticket(self.requester)
        self.url = f"{URL}{self.ticket.pk}/"
        mail.outbox.clear()  # ignore the "ticket received" notifications from the set-up

    def test_requester_cannot_change_status(self):
        response = self.client_for(self.requester).patch(self.url, {"status": "resolved"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_starting_work_assigns_the_agent(self):
        response = self.client_for(self.agent).patch(self.url, {"status": "in_progress"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "in_progress")
        self.assertEqual(response.data["assigned_to"]["username"], "meera")

    def test_resolving_requires_a_resolution_note(self):
        response = self.client_for(self.agent).patch(self.url, {"status": "resolved"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("resolution_note", response.data["errors"])

        response = self.client_for(self.agent).patch(
            self.url, {"status": "resolved", "resolution_note": "too short"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_resolve_records_who_and_when_and_notifies_requester(self):
        note = "Cleared the browser cache and re-synced the invoice service."
        response = self.client_for(self.agent).patch(
            self.url, {"status": "resolved", "resolution_note": note}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["resolution_note"], note)
        self.assertEqual(response.data["resolved_by"]["username"], "meera")
        self.assertIsNotNone(response.data["resolved_at"])

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["ragavan@acme-support.io"])
        self.assertIn("Resolved", message.subject)
        self.assertIn(note, message.body)
        html, html_type = message.alternatives[0]
        self.assertEqual(html_type, "text/html")
        self.assertIn("Your ticket has been resolved", html)
        self.assertIn(note, html)
        self.assertIn(f"/tickets/{self.ticket.pk}", html)  # "View ticket" button link

        types = list(self.ticket.activities.order_by("created_at").values_list("activity_type", flat=True))
        self.assertEqual(types, ["created", "status_changed"])

    def test_reopening_clears_resolution_metadata(self):
        client = self.client_for(self.agent)
        client.patch(self.url, {"status": "resolved", "resolution_note": "Fixed by restarting the job."},
                     format="json")
        response = client.patch(self.url, {"status": "open"}, format="json")
        self.assertEqual(response.data["status"], "open")
        self.assertIsNone(response.data["resolved_at"])

    def test_invalid_status_and_empty_update(self):
        client = self.client_for(self.agent)
        self.assertEqual(client.patch(self.url, {"status": "closed"}, format="json").status_code, 400)
        self.assertEqual(client.patch(self.url, {}, format="json").status_code, 400)

    def test_agent_can_reassign_and_change_priority(self):
        other_agent = make_user("arun", role="agent")
        response = self.client_for(self.agent).patch(
            self.url, {"assigned_to": str(other_agent.pk), "priority": str(priority("critical").pk)}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["assigned_to"]["username"], "arun")
        self.assertEqual(response.data["priority"]["code"], "critical")
        self.assertEqual(self.ticket.activities.count(), 3)

    def test_tickets_cannot_be_assigned_to_requesters(self):
        response = self.client_for(self.agent).patch(
            self.url, {"assigned_to": str(self.other_requester.pk)}, format="json"
        )
        self.assertEqual(response.status_code, 400)


class CommentsAndActivityTests(ApiTestCase):
    def test_requester_and_agent_can_comment(self):
        ticket = new_ticket(self.requester)
        url = f"{URL}{ticket.pk}/comments/"
        self.assertEqual(self.client_for(self.requester).post(url, {"message": "Any update?"}).status_code, 201)
        self.assertEqual(self.client_for(self.agent).post(url, {"message": "Looking now."}).status_code, 201)
        self.assertEqual(self.client_for(self.requester).post(url, {"message": ""}).status_code, 400)

        timeline = self.client_for(self.requester).get(f"{URL}{ticket.pk}/activities/").data
        self.assertEqual([a["activity_type"] for a in timeline], ["created", "commented", "commented"])
        self.assertEqual(timeline[-1]["note"], "Looking now.")

    def test_activity_log_is_for_agents_only(self):
        new_ticket(self.requester)
        self.assertEqual(self.client_for(self.requester).get("/api/activities/").status_code, 403)
        response = self.client_for(self.agent).get("/api/activities/?activity_type=created")
        self.assertEqual(response.data["count"], TicketActivity.objects.filter(activity_type="created").count())


class ConfigTests(ApiTestCase):
    def test_config_lists_backend_managed_options(self):
        data = self.client_for(self.requester).get("/api/config/").data
        self.assertEqual([s["value"] for s in data["statuses"]], ["open", "in_progress", "resolved"])
        self.assertEqual(len(data["categories"]), 9)
        self.assertEqual([p["code"] for p in data["priorities"]], ["low", "medium", "high", "critical"])
        self.assertEqual(data["agents"], [])  # requesters do not need the agent list

    def test_agents_receive_assignable_agents(self):
        data = self.client_for(self.agent).get("/api/config/").data
        self.assertEqual([a["username"] for a in data["agents"]], ["meera"])
