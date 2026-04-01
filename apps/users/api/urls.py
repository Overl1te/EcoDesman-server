from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    MeView,
    PublicProfileView,
    UserBanView,
    UserListView,
    UserRoleView,
    UserUnbanView,
    UserWarningView,
)

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me", MeView.as_view(), name="auth-me"),
    path("users", UserListView.as_view(), name="user-list"),
    path("users/<int:user_id>/warn", UserWarningView.as_view(), name="user-warn"),
    path("users/<int:user_id>/ban", UserBanView.as_view(), name="user-ban"),
    path("users/<int:user_id>/unban", UserUnbanView.as_view(), name="user-unban"),
    path("users/<int:user_id>/role", UserRoleView.as_view(), name="user-role"),
    path("profiles/<int:user_id>", PublicProfileView.as_view(), name="public-profile"),
]
