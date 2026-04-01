from rest_framework import serializers

from ..models import Post, PostComment, PostImage
from ..services import can_edit_comment, can_edit_post


class PostAuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source="display_name")
    avatar_url = serializers.CharField()
    role = serializers.CharField()
    status_text = serializers.CharField()


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "image_url", "position")


class PostCommentSerializer(serializers.ModelSerializer):
    author = PostAuthorSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = (
            "id",
            "body",
            "author",
            "created_at",
            "updated_at",
            "is_owner",
            "can_edit",
        )

    def get_is_owner(self, obj: PostComment) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.id == obj.author_id)

    def get_can_edit(self, obj: PostComment) -> bool:
        request = self.context.get("request")
        return bool(request and can_edit_comment(request.user, obj))


class PostListSerializer(serializers.ModelSerializer):
    author = PostAuthorSerializer(read_only=True)
    preview_text = serializers.SerializerMethodField()
    preview_image_url = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    has_images = serializers.BooleanField(read_only=True)
    is_owner = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "body",
            "preview_text",
            "kind",
            "published_at",
            "author",
            "preview_image_url",
            "likes_count",
            "comments_count",
            "favorites_count",
            "view_count",
            "is_liked",
            "is_favorited",
            "has_images",
            "is_owner",
            "can_edit",
            "event_starts_at",
            "event_ends_at",
            "event_location",
        )

    def get_preview_text(self, obj: Post) -> str:
        return obj.body[:200].strip()

    def get_preview_image_url(self, obj: Post) -> str | None:
        first_image = obj.images.first()
        return first_image.image_url if first_image else None

    def get_is_owner(self, obj: Post) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.id == obj.author_id)

    def get_can_edit(self, obj: Post) -> bool:
        request = self.context.get("request")
        return bool(request and can_edit_post(request.user, obj))


class PostDetailSerializer(serializers.ModelSerializer):
    author = PostAuthorSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    comments = PostCommentSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    favorites_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    has_images = serializers.BooleanField(read_only=True)
    is_owner = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "body",
            "kind",
            "published_at",
            "author",
            "images",
            "comments",
            "likes_count",
            "comments_count",
            "favorites_count",
            "view_count",
            "is_liked",
            "is_favorited",
            "has_images",
            "is_owner",
            "can_edit",
            "is_published",
            "event_starts_at",
            "event_ends_at",
            "event_location",
        )

    def get_is_owner(self, obj: Post) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and request.user.id == obj.author_id)

    def get_can_edit(self, obj: Post) -> bool:
        request = self.context.get("request")
        return bool(request and can_edit_post(request.user, obj))


class PostWriteSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=160)
    body = serializers.CharField(required=False)
    kind = serializers.ChoiceField(choices=Post.Kind.choices, required=False)
    is_published = serializers.BooleanField(required=False)
    image_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        allow_empty=True,
    )
    event_starts_at = serializers.DateTimeField(required=False, allow_null=True)
    event_ends_at = serializers.DateTimeField(required=False, allow_null=True)
    event_location = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate(self, attrs: dict) -> dict:
        kind = attrs.get("kind")
        if kind == Post.Kind.EVENT:
            start = attrs.get("event_starts_at")
            end = attrs.get("event_ends_at")
            location = attrs.get("event_location", "").strip()
            if start is None:
                raise serializers.ValidationError(
                    {"event_starts_at": "event_starts_at is required for events"}
                )
            if end is not None and end < start:
                raise serializers.ValidationError(
                    {"event_ends_at": "event_ends_at must be after event_starts_at"}
                )
            if not location:
                raise serializers.ValidationError(
                    {"event_location": "event_location is required for events"}
                )
        return attrs


class CommentWriteSerializer(serializers.Serializer):
    body = serializers.CharField()


class LikeStateSerializer(serializers.Serializer):
    likes_count = serializers.IntegerField()
    is_liked = serializers.BooleanField()


class FavoriteStateSerializer(serializers.Serializer):
    favorites_count = serializers.IntegerField()
    is_favorited = serializers.BooleanField()
