from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
        return Response(MapPointDetailSerializer(point).data)


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
            MapPointReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )
