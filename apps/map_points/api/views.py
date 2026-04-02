from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..selectors import get_map_point, list_active_map_points, list_map_categories
from .serializers import (
    MapPointCategorySerializer,
    MapPointDetailSerializer,
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
