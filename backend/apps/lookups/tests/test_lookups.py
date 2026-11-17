from apps.core.testing import ApiTestCase, create_default_lookups
from apps.lookups.models import LookupType, LookupValue
from apps.tickets import services


class LookupDefaultsTests(ApiTestCase):
    def test_defaults_are_created_once(self):
        create_default_lookups()  # running again must not duplicate anything
        self.assertEqual(LookupType.objects.count(), 2)
        self.assertEqual(LookupValue.objects.of_type("ticket_category").count(), 9)
        self.assertEqual(LookupValue.objects.of_type("ticket_priority").get(is_default=True).code, "medium")

    def test_only_one_default_per_type(self):
        high = LookupValue.objects.of_type("ticket_priority").get(code="high")
        high.is_default = True
        high.save()
        defaults = LookupValue.objects.of_type("ticket_priority").filter(is_default=True)
        self.assertEqual([v.code for v in defaults], ["high"])


class LookupApiTests(ApiTestCase):
    url = "/api/lookups/values/"

    def category_type(self):
        return LookupType.objects.get(code="ticket_category")

    def test_everyone_can_read_values_filtered_by_type(self):
        response = self.client_for(self.requester).get(self.url + "?type=ticket_priority&ordering=sort_order")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([v["code"] for v in response.data["results"]], ["low", "medium", "high", "critical"])

    def test_requester_cannot_change_configuration(self):
        response = self.client_for(self.requester).post(self.url, {"label": "x"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_agent_can_add_a_category_that_is_then_offered_to_users(self):
        payload = {"lookup_type": str(self.category_type().pk), "code": "hardware", "label": "Hardware",
                   "icon": "devices", "color": "#334155", "sort_order": 95}
        response = self.client_for(self.agent).post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)

        config = self.client_for(self.requester).get("/api/config/").data
        self.assertIn("hardware", [c["code"] for c in config["categories"]])

    def test_validation_errors(self):
        payload = {"lookup_type": str(self.category_type().pk), "code": "Bad Code", "label": "",
                   "color": "blue"}
        response = self.client_for(self.agent).post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.data["errors"]), {"code", "label", "color"})

    def test_duplicate_code_in_same_list_is_rejected(self):
        payload = {"lookup_type": str(self.category_type().pk), "code": "bug", "label": "Another bug"}
        response = self.client_for(self.agent).post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("code", response.data["errors"])

    def test_deactivated_values_are_hidden_from_config(self):
        value = LookupValue.objects.get(code="other")
        response = self.client_for(self.agent).patch(f"{self.url}{value.pk}/", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, 200)
        config = self.client_for(self.requester).get("/api/config/").data
        self.assertNotIn("other", [c["code"] for c in config["categories"]])

    def test_value_in_use_cannot_be_deleted(self):
        value = LookupValue.objects.get(code="bug")
        services.create_ticket(created_by=self.requester, title="Broken page", description="x" * 30,
                               category=value)
        response = self.client_for(self.agent).delete(f"{self.url}{value.pk}/")
        self.assertEqual(response.status_code, 409)
        self.assertIn("Deactivate", response.data["message"])

    def test_unused_value_can_be_deleted(self):
        value = LookupValue.objects.get(code="other")
        response = self.client_for(self.agent).delete(f"{self.url}{value.pk}/")
        self.assertEqual(response.status_code, 204)
