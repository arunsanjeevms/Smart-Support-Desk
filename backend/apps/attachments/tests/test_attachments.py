from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.attachments import storage
from apps.attachments.models import TicketAttachment
from apps.core.testing import ApiTestCase, category, priority
from apps.tickets import services
from apps.tickets.models import Ticket

PNG = b"\x89PNG\r\n\x1a\n" + bytes(64)
LOG = b"2026-11-18 10:00:01 ERROR payment gateway timed out\n"


def upload(name, content, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, content, content_type=content_type)


def attachment_limits(**overrides):
    return override_settings(SUPPORT_DESK={
        **settings.SUPPORT_DESK,
        "ATTACHMENTS": {**settings.SUPPORT_DESK["ATTACHMENTS"], **overrides},
    })


class AttachmentTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.ticket = services.create_ticket(
            created_by=self.requester,
            title="Checkout page shows an error",
            description="The checkout page shows 'Something went wrong' after I click Pay.",
            category=category("billing"),
            priority=priority("high"),
        )
        mail.outbox.clear()

    def url(self, ticket=None):
        return f"/api/tickets/{(ticket or self.ticket).pk}/attachments/"

    def send(self, *files, user=None):
        return self.client_for(user or self.requester).post(self.url(), {"files": list(files)}, format="multipart")

    def errors(self, response):
        self.assertEqual(response.status_code, 400, response.data)
        return " ".join(response.data["errors"]["files"])

    # ---- uploading ---------------------------------------------------------
    def test_requester_attaches_files_to_their_ticket(self):
        response = self.send(upload("screenshot.png", PNG, "image/png"), upload("error.log", LOG, "text/plain"))
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual([f["file_name"] for f in response.data], ["screenshot.png", "error.log"])
        self.assertEqual([f["is_image"] for f in response.data], [True, False])
        self.assertTrue(all(f["can_delete"] for f in response.data))

        detail = self.client_for(self.requester).get(f"/api/tickets/{self.ticket.pk}/").data
        self.assertEqual(len(detail["attachments"]), 2)

        timeline = self.client_for(self.requester).get(f"/api/tickets/{self.ticket.pk}/activities/").data
        entry = timeline[-1]
        self.assertEqual(entry["activity_type"], "attachment_added")
        self.assertEqual(entry["message"], "Attached 2 files")
        self.assertEqual(len(entry["attachments"]), 2)

    def test_unsupported_types_are_rejected(self):
        self.assertIn("not allowed", self.errors(self.send(upload("setup.exe", b"MZ\x90\x00"))))
        self.assertIn("not allowed", self.errors(self.send(upload("drawing.svg", b"<svg></svg>"))))

    def test_files_must_really_be_what_their_name_says(self):
        self.assertIn("does not look like a real .png", self.errors(self.send(upload("photo.png", b"MZ\x90\x00binary"))))
        self.assertIn("does not look like a real .log", self.errors(self.send(upload("app.log", b"\x00\x01\x02"))))

    @attachment_limits(MAX_FILE_MB=1)
    def test_size_limit(self):
        message = self.errors(self.send(upload("big.log", b"a" * (1024 * 1024 + 1))))
        self.assertIn("big.log is 1.0 MB; the limit is 1 MB per file", message)

    def test_number_of_files_is_limited(self):
        files = [upload(f"log-{n}.txt", LOG) for n in range(6)]
        self.assertIn("up to 5 files", self.errors(self.send(*files)))
        self.assertEqual(TicketAttachment.objects.count(), 0)

    def test_nothing_is_stored_when_one_file_is_invalid(self):
        self.errors(self.send(upload("fine.log", LOG), upload("setup.exe", b"MZ")))
        self.assertEqual(TicketAttachment.objects.count(), 0)

    # ---- who can see what ----------------------------------------------------
    def test_other_requesters_cannot_upload_or_download(self):
        attachment_id = self.send(upload("error.log", LOG)).data[0]["id"]
        self.assertEqual(self.send(upload("x.log", LOG), user=self.other_requester).status_code, 404)
        download = self.client_for(self.other_requester).get(f"/api/attachments/{attachment_id}/download/")
        self.assertEqual(download.status_code, 404)

    def test_download_returns_the_file_with_safe_headers(self):
        # The browser claims HTML - the server decides the type from the extension instead.
        attachment_id = self.send(upload("error.log", LOG, "text/html")).data[0]["id"]
        response = self.client_for(self.agent).get(f"/api/attachments/{attachment_id}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), LOG)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn('attachment; filename="error.log"', response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_only_the_uploader_or_an_agent_can_remove_a_file(self):
        agent_file = self.send(upload("agent-notes.txt", LOG), user=self.agent).data[0]
        self.assertFalse(
            self.client_for(self.requester).get(f"/api/tickets/{self.ticket.pk}/").data["attachments"][0]["can_delete"]
        )
        response = self.client_for(self.requester).delete(f"/api/attachments/{agent_file['id']}/")
        self.assertEqual(response.status_code, 403)

        own = self.send(upload("error.log", LOG)).data[0]
        file_id = TicketAttachment.objects.get(pk=own["id"]).file_id
        self.assertEqual(self.client_for(self.requester).delete(f"/api/attachments/{own['id']}/").status_code, 204)
        self.assertFalse(storage.exists(file_id))
        last = self.ticket.activities.order_by("-created_at").first()
        self.assertEqual(last.message, "Removed error.log")

    # ---- comments ------------------------------------------------------------
    def test_comment_with_files(self):
        response = self.client_for(self.requester).post(
            f"/api/tickets/{self.ticket.pk}/comments/",
            {"message": "Here is the log from this morning.", "files": [upload("error.log", LOG)]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["activity_type"], "commented")
        self.assertEqual([f["file_name"] for f in response.data["attachments"]], ["error.log"])
        # The support team's e-mail mentions the file.
        self.assertTrue(any("error.log" in message.body for message in mail.outbox))

    def test_files_without_a_message(self):
        response = self.client_for(self.requester).post(
            f"/api/tickets/{self.ticket.pk}/comments/", {"files": [upload("error.log", LOG)]}, format="multipart"
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["activity_type"], "attachment_added")

    def test_an_empty_comment_is_rejected(self):
        response = self.client_for(self.requester).post(
            f"/api/tickets/{self.ticket.pk}/comments/", {"message": "  "}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["errors"]["message"], ["Write a comment first, or attach a file."])

    # ---- housekeeping ----------------------------------------------------------
    def test_deleting_a_ticket_removes_its_stored_files(self):
        self.send(upload("screenshot.png", PNG))
        file_id = TicketAttachment.objects.get().file_id
        self.assertTrue(storage.exists(file_id))
        Ticket.objects.filter(pk=self.ticket.pk).delete()
        self.assertFalse(storage.exists(file_id))

    def test_config_tells_the_app_the_limits(self):
        config = self.client_for(self.requester).get("/api/config/").data["attachments"]
        self.assertEqual(config["max_file_mb"], 10)
        self.assertEqual(config["max_files"], 5)
        self.assertIn("png", config["allowed_extensions"])
        self.assertNotIn("svg", config["allowed_extensions"])
