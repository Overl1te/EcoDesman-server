import os
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthcheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "ЭкоВыхухоль API",
                "version": "v1",
                "timezone": settings.TIME_ZONE,
            }
        )


class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response(
                {"detail": "file is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = os.path.splitext(upload.name)[1].lower() or ".jpg"
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            return Response(
                {"detail": "unsupported file type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        relative_path = default_storage.save(
            os.path.join("uploads", f"{uuid.uuid4().hex}{extension}"),
            upload,
        )
        relative_url = f"/{settings.MEDIA_URL.strip('/')}/{relative_path}".replace("\\", "/")
        return Response(
            {
                "url": request.build_absolute_uri(relative_url),
                "path": relative_path,
            },
            status=status.HTTP_201_CREATED,
        )
