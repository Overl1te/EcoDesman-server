from rest_framework import serializers

from ..models import User
from ..selectors import get_profile_stats


class UserStatsSerializer(serializers.Serializer):
    posts_count = serializers.IntegerField()
    likes_given_count = serializers.IntegerField()
    likes_received_count = serializers.IntegerField()
    comments_count = serializers.IntegerField()
    views_received_count = serializers.IntegerField()


class UserSummarySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="display_name")
    is_banned = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "username",
            "role",
            "status_text",
            "avatar_url",
            "warning_count",
            "is_banned",
        )


class CurrentUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="display_name")
    stats = serializers.SerializerMethodField()
    is_banned = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "username",
            "email",
            "phone",
            "avatar_url",
            "role",
            "status_text",
            "bio",
            "city",
            "website_url",
            "telegram_url",
            "vk_url",
            "instagram_url",
            "warning_count",
            "is_banned",
            "stats",
        )

    def get_stats(self, obj: User) -> dict[str, int]:
        request = self.context.get("request")
        return get_profile_stats(obj, viewer=getattr(request, "user", None))


class PublicProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="display_name")
    stats = serializers.SerializerMethodField()
    is_banned = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "username",
            "avatar_url",
            "role",
            "status_text",
            "bio",
            "city",
            "website_url",
            "telegram_url",
            "vk_url",
            "instagram_url",
            "warning_count",
            "is_banned",
            "stats",
        )

    def get_stats(self, obj: User) -> dict[str, int]:
        request = self.context.get("request")
        return get_profile_stats(obj, viewer=getattr(request, "user", None))


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = CurrentUserSerializer()


class ProfileSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "display_name",
            "phone",
            "avatar_url",
            "status_text",
            "bio",
            "city",
            "website_url",
            "telegram_url",
            "vk_url",
            "instagram_url",
        )


class UserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)
