from django.test import override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.core.testing import PASSWORD, ApiTestCase, User, make_user


class LoginTests(ApiTestCase):
    url = reverse("accounts:login")

    def test_login_with_username_returns_token_and_user(self):
        response = self.anon.post(self.url, {"username": "ragavan", "password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Token.objects.filter(key=response.data["token"], user=self.requester).exists())
        self.assertEqual(response.data["user"]["role"], "requester")
        self.assertFalse(response.data["user"]["is_agent"])

    def test_login_with_email_is_supported(self):
        response = self.anon.post(self.url, {"username": "MEERA@acme-support.io", "password": PASSWORD}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["user"]["is_agent"])

    def test_wrong_password_gives_friendly_error(self):
        response = self.anon.post(self.url, {"username": "ragavan", "password": "nope"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Incorrect username or password.")

    def test_missing_fields_are_reported_per_field(self):
        response = self.anon.post(self.url, {"username": "", "password": ""}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.data["errors"])
        self.assertIn("password", response.data["errors"])


class RegisterTests(ApiTestCase):
    url = reverse("accounts:register")

    def payload(self, **overrides):
        data = {
            "username": "newuser", "email": "new@example.com", "first_name": "New",
            "last_name": "User", "password": "Sunny-Day-42", "confirm_password": "Sunny-Day-42",
        }
        data.update(overrides)
        return data

    def test_register_creates_requester_and_signs_in(self):
        response = self.anon.post(self.url, self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.role, User.Role.REQUESTER)
        self.assertIn("token", response.data)

    def test_register_cannot_choose_agent_role(self):
        self.anon.post(self.url, self.payload(role="agent"), format="json")
        self.assertEqual(User.objects.get(username="newuser").role, User.Role.REQUESTER)

    def test_password_mismatch_and_duplicates_are_rejected(self):
        response = self.anon.post(
            self.url, self.payload(confirm_password="different", email="RAGAVAN@acme-support.io", username="ragavan"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["errors"])
        self.assertIn("username", response.data["errors"])

    def test_weak_password_is_rejected(self):
        response = self.anon.post(self.url, self.payload(password="12345678", confirm_password="12345678"),
                                  format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.data["errors"])


class SessionTests(ApiTestCase):
    def test_me_requires_authentication(self):
        response = self.anon.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, 401)
        self.assertIn("sign in", response.data["message"])

    def test_me_returns_current_user(self):
        response = self.client_for(self.agent).get(reverse("accounts:me"))
        self.assertEqual(response.data["username"], "meera")

    def test_logout_deletes_token(self):
        Token.objects.create(user=self.requester)
        response = self.client_for(self.requester).post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.requester).exists())


class DemoAccountsTests(ApiTestCase):
    url = reverse("accounts:demo-accounts")

    def test_lists_only_existing_demo_accounts(self):
        # The test database has ragavan and meera; only configured accounts that exist are listed.
        response = self.anon.get(self.url)
        self.assertEqual([a["username"] for a in response.data], ["ragavan"])

    def test_lists_the_requester_agent_and_admin_buttons_in_order(self):
        make_user("arun", role=User.Role.AGENT)
        make_user("admin", role=User.Role.AGENT)
        response = self.anon.get(self.url)
        self.assertEqual(
            [(a["username"], a["label"]) for a in response.data],
            [("ragavan", "Requester"), ("arun", "Support Agent"), ("admin", "Admin")],
        )

    def test_hidden_when_demo_mode_is_off(self):
        from django.conf import settings

        with override_settings(SUPPORT_DESK={**settings.SUPPORT_DESK, "DEMO_MODE": False}):
            self.assertEqual(self.anon.get(self.url).data, [])


class UserDirectoryTests(ApiTestCase):
    def test_only_agents_can_list_users(self):
        self.assertEqual(self.client_for(self.requester).get("/api/users/").status_code, 403)
        response = self.client_for(self.agent).get("/api/users/?role=agent")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([u["username"] for u in response.data["results"]], ["meera"])

    def test_search_and_ordering(self):
        response = self.client_for(self.agent).get("/api/users/?search=kar&ordering=-username")
        self.assertEqual([u["username"] for u in response.data["results"]], ["karthik"])
