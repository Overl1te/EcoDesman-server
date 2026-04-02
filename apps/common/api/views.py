import os
import uuid
import logging

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


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
                {"detail": "Нужно выбрать файл"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = os.path.splitext(upload.name)[1].lower() or ".jpg"
        if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            return Response(
                {"detail": "Поддерживаются только JPG, PNG и WEBP"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            relative_path = default_storage.save(
                os.path.join("uploads", f"{uuid.uuid4().hex}{extension}"),
                upload,
            )
            public_url = default_storage.url(relative_path).replace("\\", "/")
            if not public_url.startswith(("http://", "https://")):
                public_url = request.build_absolute_uri(public_url)
        except Exception:
            logger.exception("Image upload failed")
            return Response(
                {"detail": "Сервис загрузки фото временно недоступен"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "url": public_url,
                "path": relative_path,
            },
            status=status.HTTP_201_CREATED,
        )
