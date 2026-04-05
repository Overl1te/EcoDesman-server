from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.support.api.serializers import ContentReportSerializer, ContentReportWriteSerializer
from apps.support.models import ContentReport
from apps.support.services import create_content_report
from apps.users.services import can_manage_posts

from ..models import MapPointReview, MapPointReviewImage
from ..selectors import get_map_point, list_active_map_points, list_map_categories
from .serializers import (
    MapPointCategorySerializer,
    MapPointDetailSerializer,
    MapPointReviewSerializer,
    MapPointReviewWriteSerializer,
    MapPointSummarySerializer,
)

MAP_BOUNDS = {
    "south": 56.230306,
    "west": 43.792757,
    "north": 56.399790,
    "east": 44.157004,
}


class MapOverviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        points = list_active_map_points()
        categories = list_map_categories()
        return Response(
            {
                "bounds": MAP_BOUNDS,
                "categories": MapPointCategorySerializer(categories, many=True).data,
                "points": MapPointSummarySerializer(points, many=True).data,
            }
        )


class MapPointDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, point_id: int):
        point = get_object_or_404(get_map_point(point_id))
        return Response(MapPointDetailSerializer(point, context={"request": request}).data)


class MapPointReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, point_id: int):
        point = get_object_or_404(get_map_point(point_id))
        serializer = MapPointReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        display_name = request.user.display_name or request.user.username
        review = MapPointReview.objects.create(
            point=point,
            author=request.user,
            author_name=display_name,
            rating=serializer.validated_data["rating"],
            body=serializer.validated_data["body"].strip(),
        )
        image_urls = serializer.validated_data.get("image_urls", [])
        if image_urls:
            MapPointReviewImage.objects.bulk_create(
                [
                    MapPointReviewImage(
                        review=review,
                        image_url=image_url,
                        position=index,
                    )
                    for index, image_url in enumerate(image_urls)
                ]
            )
            review = (
                MapPointReview.objects.select_related("author")
                .prefetch_related("images")
                .get(id=review.id)
            )

        return Response(
            MapPointReviewSerializer(review, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MapPointReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, point_id: int, review_id: int):
        review = get_object_or_404(MapPointReview, id=review_id, point_id=point_id)
        if request.user.id != review.author_id and not can_manage_posts(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MapPointReviewReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, point_id: int, review_id: int):
        review = get_object_or_404(MapPointReview, id=review_id, point_id=point_id)
        serializer = ContentReportWriteSerializer(
            data={
                **request.data,
                "target_type": ContentReport.TargetType.MAP_REVIEW,
                "target_id": review.id,
            }
        )
        serializer.is_valid(raise_exception=True)
        report = create_content_report(
            reporter=request.user,
            target_type=ContentReport.TargetType.MAP_REVIEW,
            target=review,
            target_snapshot=review.body[:80] or f"Отзыв #{review.id}",
            reason=serializer.validated_data["reason"],
            details=serializer.validated_data.get("details", ""),
        )
        return Response(
            ContentReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
