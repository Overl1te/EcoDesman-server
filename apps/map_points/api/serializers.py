from rest_framework import serializers

from ..models import MapPoint, MapPointCategory, MapPointImage, MapPointReview


class MapPointCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MapPointCategory
        fields = ("id", "slug", "title")


class MapPointImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapPointImage
        fields = ("id", "image_url", "caption", "position")


class MapPointReviewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField()

    class Meta:
        model = MapPointReview
        fields = ("id", "author_name", "rating", "body", "created_at")


class MapPointSummarySerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    categories = MapPointCategorySerializer(many=True)
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
            "cover_image_url",
        )

    def get_cover_image_url(self, obj: MapPoint) -> str:
        first_image = next(iter(obj.images.all()), None)
        return first_image.image_url if first_image else ""


class MapPointDetailSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    categories = MapPointCategorySerializer(many=True)
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
            "images",
            "reviews",
        )
