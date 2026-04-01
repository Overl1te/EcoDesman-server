import importlib
from urllib.parse import urlsplit

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import clear_url_caches, reverse

from apps.users.models import User


class ImageUploadViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="uploader",
            email="uploader@econizhny.local",
            password="demo12345",
        )

    def login(self) -> str:
        response = self.client.post(
            reverse("auth-login"),
            {
                "identifier": "uploader@econizhny.local",
                "password": "demo12345",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["access"]

    def test_authenticated_user_can_upload_image(self):
        access_token = self.login()
        upload = SimpleUploadedFile(
            "avatar.png",
            b"\x89PNG\r\n\x1a\nmock-image-content",
            content_type="image/png",
        )

        response = self.client.post(
            reverse("image-upload"),
            {"file": upload},
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("/media/uploads/", response.json()["url"])

    @override_settings(DEBUG=False, SERVE_MEDIA_FILES=True)
    def test_uploaded_image_is_publicly_accessible_when_media_serving_enabled(self):
        import config.urls as root_urls

        clear_url_caches()
        importlib.reload(root_urls)

        access_token = self.login()
        upload = SimpleUploadedFile(
            "public-avatar.png",
            b"\x89PNG\r\n\x1a\npublic-image-content",
            content_type="image/png",
        )

        response = self.client.post(
            reverse("image-upload"),
            {"file": upload},
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 201)
        media_path = urlsplit(response.json()["url"]).path

        media_response = self.client.get(media_path)

        self.assertEqual(media_response.status_code, 200)
        self.assertEqual(
            b"".join(media_response.streaming_content),
            b"\x89PNG\r\n\x1a\npublic-image-content",
        )
