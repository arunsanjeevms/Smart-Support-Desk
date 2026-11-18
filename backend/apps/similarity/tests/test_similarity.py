from unittest import skipUnless

import numpy as np
from django.conf import settings
from django.test import override_settings

from apps.core.testing import ApiTestCase, category, priority
from apps.similarity.constants import KEYWORD, SEMANTIC
from apps.similarity.engines import semantic_installed
from apps.similarity.models import TicketEmbedding
from apps.similarity.services import find_similar
from apps.tickets import services
from apps.tickets.constants import TicketStatus
from apps.tickets.management.commands._demo_data import TICKETS as DEMO_TICKETS
from apps.tickets.models import Ticket, TicketActivity

URL = "/api/tickets/similar/"


def similarity(**overrides):
    """Run a test with some of the SUPPORT_DESK["SIMILARITY"] settings changed."""
    return override_settings(SUPPORT_DESK={
        **settings.SUPPORT_DESK,
        "SIMILARITY": {**settings.SUPPORT_DESK["SIMILARITY"], **overrides},
    })


class SimilarityTestCase(ApiTestCase):
    def resolved(self, title, description, *, code="bug", note="Found the cause and fixed it for the customer."):
        ticket = services.create_ticket(
            created_by=self.other_requester,
            title=title,
            description=description,
            category=category(code),
            priority=priority("medium"),
        )
        services.update_ticket(
            ticket=ticket, actor=self.agent, changes={"status": TicketStatus.RESOLVED, "resolution_note": note}
        )
        ticket.refresh_from_db()
        return ticket

    def search(self, user=None, **payload):
        return self.client_for(user or self.requester).post(URL, payload, format="json")


@similarity(ENGINE=KEYWORD)
class SimilarTicketsApiTests(SimilarityTestCase):
    """The endpoint, using keyword matching so the tests are fast and need no model."""

    def setUp(self):
        super().setUp()
        self.invoices = self.resolved(
            "Invoice download button does nothing",
            "Clicking download on any invoice does nothing in Chrome.",
            code="billing",
            note="Pop-ups were blocked for the billing site. Allowed them and the download works.",
        )
        self.dates = self.resolved(
            "Excel export shows wrong dates", "Every date in the exported sales report is one day early.",
            code="data_reports",
        )
        self.login = self.resolved(
            "Cannot log in after password reset", "The login page says invalid credentials after a reset.",
            code="login_access",
        )
        # Same problem, but not resolved yet - must never be suggested.
        self.still_open = services.create_ticket(
            created_by=self.other_requester,
            title="Invoice download is broken",
            description="The invoice download button does nothing at all.",
            category=category("billing"),
            priority=priority("medium"),
        )

    def test_requires_sign_in(self):
        self.assertEqual(self.anon.post(URL, {"title": "Invoice download"}, format="json").status_code, 401)

    def test_needs_some_text_to_compare(self):
        response = self.search(title="Help")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["message"], "Add a title or a short description first, so there is something to compare."
        )

    def test_returns_resolved_tickets_best_match_first(self):
        response = self.search(title="Invoice download not working", description="The download button does nothing.")
        self.assertEqual(response.status_code, 200, response.data)
        results = response.data["results"]
        self.assertEqual(response.data["engine"], KEYWORD)
        self.assertEqual(response.data["compared"], 3)
        self.assertEqual(results[0]["id"], str(self.invoices.pk))
        self.assertEqual(results[0]["resolution_note"], self.invoices.resolution_note)
        self.assertEqual(results[0]["category"]["code"], "billing")
        self.assertNotIn(str(self.still_open.pk), [r["id"] for r in results])
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(0 < s <= 1 for s in scores))

    def test_never_more_than_three_suggestions(self):
        for number in range(4):
            self.resolved(f"Invoice download fails {number}", "The invoice download button does nothing.")
        results = self.search(title="Invoice download button does nothing").data["results"]
        self.assertEqual(len(results), 3)

    def test_unrelated_text_gets_no_suggestions(self):
        response = self.search(description="The office coffee machine is leaking water again")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_requesters_see_other_peoples_fixes_but_not_who_raised_them(self):
        result = self.search(title="Invoice download does nothing").data["results"][0]
        self.assertEqual(result["id"], str(self.invoices.pk))  # raised by another requester
        self.assertNotIn("created_by", result)
        self.assertEqual(set(result["resolved_by"]), {"full_name", "initials"})

    def test_suggestions_are_advisory_and_change_nothing(self):
        before = {t.pk: (t.status, t.updated_at) for t in Ticket.objects.all()}
        activity_count = TicketActivity.objects.count()
        self.search(title="Invoice download not working", description="The download button does nothing.")
        self.assertEqual({t.pk: (t.status, t.updated_at) for t in Ticket.objects.all()}, before)
        self.assertEqual(TicketActivity.objects.count(), activity_count)

    def test_exclude_leaves_a_ticket_out(self):
        results = self.search(title="Invoice download does nothing", exclude=str(self.invoices.pk)).data["results"]
        self.assertNotIn(str(self.invoices.pk), [r["id"] for r in results])

    def test_reopened_tickets_are_no_longer_suggested(self):
        services.update_ticket(ticket=self.invoices, actor=self.agent, changes={"status": TicketStatus.OPEN})
        results = self.search(title="Invoice download does nothing").data["results"]
        self.assertNotIn(str(self.invoices.pk), [r["id"] for r in results])

    def test_config_describes_the_feature(self):
        config = self.client_for(self.requester).get("/api/config/").data["similarity"]
        self.assertEqual(config, {"enabled": True, "max_results": 3, "min_length": 10})

    @similarity(ENABLED=False, ENGINE=KEYWORD)
    def test_can_be_switched_off(self):
        self.assertEqual(self.search(title="Invoice download does nothing").status_code, 404)
        self.assertFalse(self.client_for(self.requester).get("/api/config/").data["similarity"]["enabled"])


class FakeEngine:
    """Stands in for the model: counts what gets encoded (vectors from letter counts)."""

    name = SEMANTIC
    needs_index = True

    def __init__(self, model_name="fake-model-v1"):
        self.model_name = model_name
        self.encoded = []

    def encode(self, texts):
        self.encoded.extend(texts)
        vectors = np.zeros((len(texts), 26), dtype=np.float32)
        for row, text in enumerate(texts):
            for char in text.lower():
                if "a" <= char <= "z":
                    vectors[row, ord(char) - 97] += 1
        return vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9)


class EmbeddingCacheTests(SimilarityTestCase):
    """Resolved tickets are encoded once and cached in MongoDB."""

    def setUp(self):
        super().setUp()
        self.first = self.resolved("Invoice download does nothing", "Clicking download on an invoice does nothing.")
        self.second = self.resolved("Dashboard is very slow", "The dashboard takes a minute to load.")

    def test_each_resolved_ticket_is_encoded_once(self):
        engine = FakeEngine()
        find_similar(title="Invoice download", engine=engine)
        self.assertEqual(len(engine.encoded), 3)  # two tickets + the new text
        self.assertEqual(TicketEmbedding.objects.count(), 2)

        engine.encoded.clear()
        find_similar(title="Invoice download", engine=engine)
        self.assertEqual(engine.encoded, ["Invoice download"])  # only the new text

    def test_changed_text_or_model_is_encoded_again(self):
        find_similar(title="Invoice download", engine=FakeEngine())
        Ticket.objects.filter(pk=self.first.pk).update(title="Invoice download button is greyed out")

        engine = FakeEngine()
        find_similar(title="Invoice download", engine=engine)
        self.assertEqual(len(engine.encoded), 2)  # the changed ticket + the new text

        engine = FakeEngine("fake-model-v2")
        find_similar(title="Invoice download", engine=engine)
        self.assertEqual(len(engine.encoded), 3)  # a new model encodes everything again
        self.assertEqual(set(TicketEmbedding.objects.values_list("model_name", flat=True)), {"fake-model-v2"})


@skipUnless(semantic_installed(), "sentence-transformers is not installed")
@similarity(ENGINE=SEMANTIC)
class SentenceTransformerTests(SimilarityTestCase):
    """The real model: different wording still finds the right resolved ticket."""

    def setUp(self):
        super().setUp()
        for spec in DEMO_TICKETS:
            if spec["status"] == TicketStatus.RESOLVED:
                self.resolved(spec["title"], spec["description"], code=spec["category"], note=spec["resolution"])

    def suggestions(self, text):
        response = self.search(description=text)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["engine"], SEMANTIC, "the model could not be loaded")
        return response.data["results"]

    def test_different_wording_still_finds_the_same_problem(self):
        cases = {
            # Hardly any words in common with the resolved ticket:
            "The analytics page is painfully slow to open": "Dashboard takes more than a minute to load",
            "Unable to get into my account since I changed my credentials": "Cannot log in after resetting my password",
            "The verification number from my phone is never valid": "Two-factor codes not accepted",
            "I was billed two times for this month's plan": "Charged twice for the monthly subscription",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                results = self.suggestions(text)
                self.assertTrue(results, "no suggestion at all")
                self.assertEqual(results[0]["title"], expected)

    def test_unrelated_issue_gets_no_suggestions(self):
        self.assertEqual(self.suggestions("The office printer is out of toner"), [])
