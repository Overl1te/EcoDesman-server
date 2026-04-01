from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

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
