from apps.core.testing import category, priority
from apps.lookups.models import LookupValue
from apps.similarity.constants import KEYWORD
from apps.tickets import services
from apps.tickets.models import Ticket

from .test_similarity import SimilarityTestCase, similarity

URL = "/api/tickets/suggest-category/"


@similarity(ENGINE=KEYWORD)
class CategorySuggestionTests(SimilarityTestCase):
    """Category suggestions, using keyword matching so the tests are fast and need no model."""

    def setUp(self):
        super().setUp()
        for title, description in [
            ("Invoice download button does nothing", "Clicking download on any invoice does nothing."),
            ("Charged twice for the subscription", "Our card shows two charges on the invoice this month."),
            ("Refund for a cancelled plan", "We cancelled the plan but the invoice was still charged."),
        ]:
            self.resolved(title, description, code="billing")
        for title, description in [
            ("Dashboard is very slow", "The dashboard page takes a minute to load every morning."),
            ("Reports time out", "The yearly report page times out after a minute."),
        ]:
            self.resolved(title, description, code="performance")

    def suggest(self, **payload):
        return self.client_for(self.requester).post(URL, payload, format="json")

    def test_suggests_the_category_of_similar_tickets(self):
        response = self.suggest(title="Invoice download not working", description="The invoice download button does nothing")
        self.assertEqual(response.status_code, 200, response.data)
        suggestion = response.data["suggestion"]
        self.assertEqual(suggestion["category"]["code"], "billing")
        self.assertEqual(suggestion["basis"], "similar_tickets")
        self.assertGreaterEqual(suggestion["matches"], 1)
        self.assertGreaterEqual(suggestion["confidence"], 0.5)
        self.assertEqual(response.data["engine"], KEYWORD)
        # Only the category comes back - nothing about other people's tickets.
        self.assertEqual(set(suggestion), {"category", "confidence", "basis", "matches"})

    def test_open_tickets_count_too(self):
        services.create_ticket(
            created_by=self.other_requester,
            title="Webhook signature mismatch",
            description="Every webhook delivery fails with a signature mismatch error.",
            category=category("integration"),
            priority=priority("high"),
        )
        suggestion = self.suggest(description="Webhook deliveries fail: signature mismatch").data["suggestion"]
        self.assertEqual(suggestion["category"]["code"], "integration")

    def test_unrelated_text_gets_no_suggestion(self):
        response = self.suggest(description="The office coffee machine is leaking water again")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["suggestion"])

    def test_inactive_categories_are_never_suggested(self):
        LookupValue.objects.filter(pk=category("billing").pk).update(is_active=False)
        suggestion = self.suggest(title="Invoice download button does nothing").data["suggestion"]
        self.assertTrue(suggestion is None or suggestion["category"]["code"] != "billing")

    def test_falls_back_to_the_category_descriptions(self):
        # No tickets at all yet (e.g. a new desk, or a category added on the Configuration screen).
        Ticket.objects.all().delete()
        suggestion = self.suggest(description="Refund for the charges on our invoices").data["suggestion"]
        self.assertEqual(suggestion["category"]["code"], "billing")
        self.assertEqual(suggestion["basis"], "category_description")
        self.assertEqual(suggestion["matches"], 0)

    def test_needs_some_text(self):
        response = self.suggest(title="Help")
        self.assertEqual(response.status_code, 400)

    @similarity(ENGINE=KEYWORD, CATEGORY_SUGGESTIONS=False)
    def test_can_be_switched_off(self):
        self.assertEqual(self.suggest(title="Invoice download button does nothing").status_code, 404)
        config = self.client_for(self.requester).get("/api/config/").data["similarity"]
        self.assertFalse(config["category_suggestions"])
