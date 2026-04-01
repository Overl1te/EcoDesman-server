from django.test import TestCase
from django.urls import reverse

from apps.posts.models import Post
from apps.users.models import User


class AuthApiTests(TestCase):
    def login(self, identifier="anna@econizhny.local", password="demo12345") -> str:
        response = self.client.post(
            reverse("auth-login"),
            {
                "identifier": identifier,
                "password": password,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["access"]

    def test_login_returns_tokens(self):
        response = self.client.post(
            reverse("auth-login"),
            {
                "identifier": "anna@econizhny.local",
                "password": "demo12345",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())
        self.assertEqual(response.json()["user"]["role"], "user")

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
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status_text"], "Обновил профиль")
        self.assertEqual(response.json()["city"], "Bor")
        self.assertEqual(response.json()["website_url"], "https://econizhny.local")
        self.assertEqual(response.json()["telegram_url"], "https://t.me/econizhny")

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
