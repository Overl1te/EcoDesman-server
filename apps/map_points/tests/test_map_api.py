from django.test import TestCase
from django.urls import reverse

from apps.map_points.models import MapPoint


class MapApiTests(TestCase):
    def test_map_overview_returns_categories_and_point_summaries(self):
        hidden_point = MapPoint.objects.create(
            slug="hidden-point",
            title="Скрытая точка",
            short_description="Не должна отображаться",
            latitude=56.300000,
            longitude=44.000000,
            is_active=False,
            sort_order=999,
        )

        response = self.client.get(reverse("map-overview"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["bounds"]["south"], 56.230306)
        self.assertEqual(payload["bounds"]["east"], 44.157004)
        self.assertGreaterEqual(len(payload["categories"]), 5)
        self.assertGreaterEqual(len(payload["points"]), 5)
        self.assertNotIn(hidden_point.slug, [item["slug"] for item in payload["points"]])

        first_point = payload["points"][0]
        self.assertIn("categories", first_point)
        self.assertIn("short_description", first_point)
        self.assertIn("cover_image_url", first_point)

    def test_map_point_detail_returns_gallery_reviews_and_metadata(self):
        point = MapPoint.objects.get(slug="ecopunkt")

        response = self.client.get(
            reverse("map-point-detail", kwargs={"point_id": point.id})
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "ecopunkt")
        self.assertGreaterEqual(len(payload["images"]), 2)
        self.assertGreaterEqual(len(payload["reviews"]), 1)
        self.assertGreaterEqual(len(payload["categories"]), 1)
        self.assertTrue(payload["description"])
        self.assertTrue(payload["address"])
