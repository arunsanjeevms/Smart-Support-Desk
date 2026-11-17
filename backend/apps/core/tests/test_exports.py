from io import BytesIO

from django.core import mail
from openpyxl import load_workbook

from apps.core.sequences import next_sequence
from apps.core.testing import ApiTestCase, category
from apps.tickets import services


class ExportTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.login_ticket = services.create_ticket(
            created_by=self.requester, title="Cannot sign in on mobile",
            description="The mobile app rejects my password every time.", category=category("login_access"),
        )
        services.create_ticket(
            created_by=self.other_requester, title="Refund for duplicate charge",
            description="We were charged twice for the same invoice.", category=category("billing"),
        )

    def test_excel_export_contains_the_filtered_rows(self):
        response = self.client_for(self.agent).get("/api/tickets/export/?file_type=xlsx&search=sign")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])
        self.assertIn('attachment; filename="tickets-', response["Content-Disposition"])

        sheet = load_workbook(BytesIO(response.content)).active
        self.assertEqual(sheet["A4"].value, "Reference")
        self.assertEqual(sheet["A5"].value, self.login_ticket.reference)
        self.assertIsNone(sheet["A6"].value)  # only one row matches the search
        self.assertIn('Search: "sign"', sheet["A2"].value)

    def test_pdf_export(self):
        response = self.client_for(self.agent).get("/api/tickets/export/?file_type=pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_pdf_embeds_the_poppins_font(self):
        response = self.client_for(self.agent).get("/api/tickets/export/?file_type=pdf")
        self.assertIn(b"Poppins", response.content)
        self.assertIn(b"Poppins-SemiBold", response.content)

    def test_pdf_with_no_matching_rows_still_renders(self):
        response = self.client_for(self.agent).get("/api/tickets/export/?file_type=pdf&search=nothing-matches")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_requester_export_only_contains_own_tickets(self):
        response = self.client_for(self.requester).get("/api/tickets/export/?file_type=xlsx")
        sheet = load_workbook(BytesIO(response.content)).active
        self.assertEqual(sheet["A5"].value, self.login_ticket.reference)
        self.assertIsNone(sheet["A6"].value)

    def test_unknown_format_is_rejected(self):
        response = self.client_for(self.agent).get("/api/tickets/export/?file_type=docx")
        self.assertEqual(response.status_code, 400)
        self.assertIn("file_type", response.data["errors"])

    def test_every_table_supports_export(self):
        client = self.client_for(self.agent)
        for url in ("/api/activities/", "/api/users/", "/api/lookups/values/"):
            with self.subTest(url=url):
                response = client.get(url + "export/?file_type=pdf")
                self.assertEqual(response.status_code, 200)

    def test_email_export_sends_attachment(self):
        response = self.client_for(self.agent).post(
            "/api/tickets/export/email/?status=open",
            {"file_type": "pdf", "recipients": ["lead@example.com", "LEAD@example.com"], "message": "FYI"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["lead@example.com"])
        self.assertEqual(message.body, "FYI")
        filename, content, mimetype = message.attachments[0]
        self.assertTrue(filename.endswith(".pdf"))
        self.assertEqual(mimetype, "application/pdf")

    def test_email_export_validates_recipients(self):
        response = self.client_for(self.agent).post(
            "/api/tickets/export/email/", {"file_type": "pdf", "recipients": ["not-an-email"]}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("recipients", response.data["errors"])
        self.assertEqual(len(mail.outbox), 0)


class SequenceTests(ApiTestCase):
    def test_sequence_starts_at_given_value_and_increments(self):
        self.assertEqual(next_sequence("demo", start=500), 500)
        self.assertEqual(next_sequence("demo", start=500), 501)
        self.assertEqual(next_sequence("other"), 1)


class HealthTests(ApiTestCase):
    def test_health_endpoint_is_public(self):
        response = self.anon.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["database"], "up")
