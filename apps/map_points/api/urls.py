from django.urls import path

from .views import MapOverviewView, MapPointDetailView, MapPointReviewCreateView

urlpatterns = [
    path("map/overview", MapOverviewView.as_view(), name="map-overview"),
    path("map/points/<int:point_id>", MapPointDetailView.as_view(), name="map-point-detail"),
    path(
        "map/points/<int:point_id>/reviews",
        MapPointReviewCreateView.as_view(),
        name="map-point-review-create",
    ),
]
