from django.db.models import Prefetch

from .models import MapPoint, MapPointCategory, MapPointImage, MapPointReview


def list_active_map_points():
    return (
        MapPoint.objects.filter(is_active=True)
        .prefetch_related("categories")
        .prefetch_related(
            Prefetch("images", queryset=MapPointImage.objects.order_by("position", "id")),
            Prefetch("reviews", queryset=MapPointReview.objects.order_by("-created_at", "-id")),
        )
    )


def get_map_point(point_id: int):
    return list_active_map_points().filter(id=point_id)


def list_map_categories():
    return MapPointCategory.objects.order_by("sort_order", "title", "id")
