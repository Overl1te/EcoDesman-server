from django.test import TestCase
from django.urls import reverse


class HealthcheckViewTests(TestCase):
    def test_healthcheck_returns_ok(self):
        response = self.client.get(reverse("healthcheck"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
