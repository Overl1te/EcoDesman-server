from django.test import TestCase
from django.urls import reverse

from apps.posts.models import Post
from apps.users.models import User


class AuthApiTests(TestCase):
    def login_payload(self, identifier="anna@econizhny.local", password="demo12345") -> dict:
        response = self.client.post(
            reverse("auth-login"),
            {
                "identifier": identifier,
                "password": password,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def login(self, identifier="anna@econizhny.local", password="demo12345") -> str:
        return self.login_payload(identifier=identifier, password=password)["access"]

    def test_login_returns_tokens(self):
        payload = self.login_payload()

        self.assertIn("access", payload)
        self.assertIn("refresh", payload)
        self.assertEqual(payload["user"]["role"], "user")

    def test_register_returns_tokens_and_creates_user(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "username": "newuser",
                "email": "newuser@econizhny.local",
                "display_name": "New User",
                "phone": "+7 (999) 123-45-67",
                "password": "StrongPass123",
                "password_confirmation": "StrongPass123",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertEqual(response.json()["user"]["username"], "newuser")
        self.assertEqual(response.json()["user"]["phone"], "+79991234567")
        self.assertTrue(
            User.objects.filter(email="newuser@econizhny.local", username="newuser").exists(),
        )

    def test_register_rejects_duplicate_identity_fields_case_insensitively(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "username": "Anna",
                "email": "ANNA@econizhny.local",
                "password": "StrongPass123",
                "password_confirmation": "StrongPass123",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("username", response.json())
        self.assertIn("email", response.json())

    def test_me_returns_current_user(self):
        access_token = self.login()

        response = self.client.get(
            reverse("auth-me"),
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "anna@econizhny.local")
        self.assertIn("stats", response.json())

    def test_me_patch_updates_profile_settings(self):
        access_token = self.login()

        response = self.client.patch(
            reverse("auth-me"),
            {
                "status_text": "Обновил профиль",
                "city": "Bor",
                "website_url": "https://econizhny.local",
                "telegram_url": "https://t.me/econizhny",
                "username": "anna_updated",
                "email": "anna.updated@econizhny.local",
                "phone": "8 (950) 123-45-67",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status_text"], "Обновил профиль")
        self.assertEqual(response.json()["city"], "Bor")
        self.assertEqual(response.json()["website_url"], "https://econizhny.local")
        self.assertEqual(response.json()["telegram_url"], "https://t.me/econizhny")
        self.assertEqual(response.json()["username"], "anna_updated")
        self.assertEqual(response.json()["email"], "anna.updated@econizhny.local")
        self.assertEqual(response.json()["phone"], "+79501234567")

    def test_logout_blacklists_refresh_token(self):
        payload = self.login_payload()

        logout_response = self.client.post(
            reverse("auth-logout"),
            {"refresh": payload["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(logout_response.status_code, 204)

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": payload["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_change_password_rotates_session_and_invalidates_old_credentials(self):
        payload = self.login_payload()

        response = self.client.post(
            reverse("auth-change-password"),
            {
                "current_password": "demo12345",
                "new_password": "new-demo12345",
                "new_password_confirmation": "new-demo12345",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {payload['access']}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

        old_login_response = self.client.post(
            reverse("auth-login"),
            {
                "identifier": "anna@econizhny.local",
                "password": "demo12345",
            },
            content_type="application/json",
        )
        self.assertEqual(old_login_response.status_code, 401)

        new_login_response = self.client.post(
            reverse("auth-login"),
            {
                "identifier": "anna@econizhny.local",
                "password": "new-demo12345",
            },
            content_type="application/json",
        )
        self.assertEqual(new_login_response.status_code, 200)

        old_refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": payload["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(old_refresh_response.status_code, 401)

    def test_public_profile_hides_draft_posts_from_public_stats(self):
        user = User.objects.create_user(
            username="draft_owner",
            email="draft-owner@econizhny.local",
            password="demo12345",
        )
        Post.objects.create(author=user, title="Published", body="Visible", is_published=True)
        Post.objects.create(author=user, title="Draft", body="Hidden", is_published=False)

        public_response = self.client.get(reverse("public-profile", kwargs={"user_id": user.id}))
        self.assertEqual(public_response.status_code, 200)
        self.assertEqual(public_response.json()["stats"]["posts_count"], 1)

        access_token = self.login(identifier="draft-owner@econizhny.local")
        me_response = self.client.get(
            reverse("auth-me"),
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["stats"]["posts_count"], 2)

    def test_user_search_filters_by_username(self):
        response = self.client.get(reverse("user-list"), {"search": "anna"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["username"] == "anna" for item in response.json()))

    def test_admin_can_warn_user_until_auto_ban(self):
        admin_token = self.login(identifier="admin@econizhny.local")
        target = User.objects.get(email="anna@econizhny.local")

        for expected_warnings in range(1, 6):
            response = self.client.post(
                reverse("user-warn", kwargs={"user_id": target.id}),
                HTTP_AUTHORIZATION=f"Bearer {admin_token}",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["warning_count"], expected_warnings)

        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertTrue(target.is_banned)

        login_response = self.client.post(
            reverse("auth-login"),
            {
                "identifier": "anna@econizhny.local",
                "password": "demo12345",
            },
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 403)

    def test_banned_user_refresh_is_rejected(self):
        payload = self.login_payload()
        target = User.objects.get(email="anna@econizhny.local")
        target.is_active = False
        target.warning_count = 5
        target.save(update_fields=["is_active", "warning_count"])

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": payload["refresh"]},
            content_type="application/json",
        )
        self.assertEqual(refresh_response.status_code, 403)

    def test_admin_can_unban_and_change_role(self):
        admin_token = self.login(identifier="admin@econizhny.local")
        target = User.objects.get(email="anna@econizhny.local")
        target.is_active = False
        target.warning_count = 5
        target.save(update_fields=["is_active", "warning_count"])

        unban_response = self.client.post(
            reverse("user-unban", kwargs={"user_id": target.id}),
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(unban_response.status_code, 200)
        self.assertEqual(unban_response.json()["warning_count"], 0)
        self.assertFalse(unban_response.json()["is_banned"])

        role_response = self.client.patch(
            reverse("user-role", kwargs={"user_id": target.id}),
            {"role": "moderator"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(role_response.status_code, 200)
        self.assertEqual(role_response.json()["role"], "moderator")
