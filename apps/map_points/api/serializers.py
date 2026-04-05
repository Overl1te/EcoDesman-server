from rest_framework import serializers

from apps.users.services import can_manage_posts

from ..category_style import sort_categories
from ..models import (
    MapPoint,
    MapPointCategory,
    MapPointImage,
    MapPointReview,
    MapPointReviewImage,
)


class MapPointCategorySerializer(serializers.ModelSerializer):
    sort_order = serializers.IntegerField(source="priority", read_only=True)
    color = serializers.CharField(source="marker_color", read_only=True)

    class Meta:
        model = MapPointCategory
        fields = ("id", "slug", "title", "sort_order", "color")


class MapPointImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapPointImage
        fields = ("id", "image_url", "caption", "position")


class MapPointReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapPointReviewImage
        fields = ("id", "image_url", "caption", "position")


class MapPointReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    images = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = MapPointReview
        fields = (
            "id",
            "author_name",
            "rating",
            "body",
            "created_at",
            "images",
            "is_owner",
            "can_edit",
        )

    def get_author_name(self, obj: MapPointReview) -> str:
        if obj.author_name:
            return obj.author_name

        if obj.author:
            return obj.author.display_name or obj.author.username

        return "Пользователь"


    def get_images(self, obj: MapPointReview):
        return MapPointReviewImageSerializer(obj.images.all(), many=True).data

    def get_is_owner(self, obj: MapPointReview) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.id == obj.author_id)

    def get_can_edit(self, obj: MapPointReview) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and (request.user.id == obj.author_id or can_manage_posts(request.user))
        )


class MapPointReviewWriteSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    body = serializers.CharField(min_length=3, max_length=2000)
    image_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        allow_empty=True,
    )


class BaseMapPointSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    categories = serializers.SerializerMethodField()
    primary_category = serializers.SerializerMethodField()

    def _sorted_categories(self, obj: MapPoint) -> list[MapPointCategory]:
        return sort_categories(obj.categories.all())

    def get_categories(self, obj: MapPoint):
        return MapPointCategorySerializer(self._sorted_categories(obj), many=True).data

    def get_primary_category(self, obj: MapPoint):
        categories = self._sorted_categories(obj)
        if not categories:
            return None
        return MapPointCategorySerializer(categories[0]).data


class MapPointSummarySerializer(BaseMapPointSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = MapPoint
        fields = (
            "id",
            "slug",
            "title",
            "short_description",
            "latitude",
            "longitude",
            "categories",
            "primary_category",
            "cover_image_url",
        )

    def get_cover_image_url(self, obj: MapPoint) -> str:
        first_image = next(iter(obj.images.all()), None)
        return first_image.image_url if first_image else ""


class MapPointDetailSerializer(BaseMapPointSerializer):
    images = MapPointImageSerializer(many=True)
    reviews = MapPointReviewSerializer(many=True)

    class Meta:
        model = MapPoint
        fields = (
            "id",
            "slug",
            "title",
            "short_description",
            "description",
            "address",
            "working_hours",
            "latitude",
            "longitude",
            "categories",
            "primary_category",
            "images",
            "reviews",
        )
