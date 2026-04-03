from django.urls import include, path
from apps.common.api.views import ImageUploadView

urlpatterns = [
    path("health/", include("apps.common.api.urls")),
    path("uploads/images", ImageUploadView.as_view(), name="image-upload"),
    path("", include("apps.admin_panel.api.urls")),
    path("", include("apps.users.api.urls")),
    path("", include("apps.map_points.api.urls")),
    path("", include("apps.notifications.api.urls")),
    path("", include("apps.posts.api.urls")),
]
