from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import User
from ..selectors import search_users
from ..services import (
    authenticate_user,
    ban_user,
    can_administrate,
    get_user_by_identifier,
    issue_warning,
    unban_user,
    update_user_role,
)
from .serializers import (
    CurrentUserSerializer,
    LoginSerializer,
    ProfileSettingsSerializer,
    PublicProfileSerializer,
    UserRoleSerializer,
    UserSummarySerializer,
)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate_user(
            identifier=serializer.validated_data["identifier"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            existing_user = get_user_by_identifier(serializer.validated_data["identifier"])
            if existing_user and not existing_user.is_active:
                return Response(
                    {"detail": "Аккаунт заблокирован"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response(
                {"detail": "Неверный логин или пароль"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": CurrentUserSerializer(user, context={"request": request}).data,
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        serializer = ProfileSettingsSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CurrentUserSerializer(request.user, context={"request": request}).data)


class UserListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = search_users(request.query_params.get("search"))[:20]
        serializer = UserSummarySerializer(queryset, many=True)
        return Response(serializer.data)


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id: int):
        user = get_object_or_404(User, id=user_id)
        return Response(PublicProfileSerializer(user, context={"request": request}).data)


class UserWarningView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id: int):
        if not can_administrate(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, id=user_id)
        issue_warning(user)
        return Response(PublicProfileSerializer(user, context={"request": request}).data)


class UserBanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id: int):
        if not can_administrate(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, id=user_id)
        ban_user(user)
        return Response(PublicProfileSerializer(user, context={"request": request}).data)


class UserUnbanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id: int):
        if not can_administrate(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, id=user_id)
        unban_user(user)
        return Response(PublicProfileSerializer(user, context={"request": request}).data)


class UserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, user_id: int):
        if not can_administrate(request.user):
            return Response(status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, id=user_id)
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_user_role(user, serializer.validated_data["role"])
        return Response(PublicProfileSerializer(user, context={"request": request}).data)
