from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class Post(TimeStampedModel):
    class Kind(models.TextChoices):
        NEWS = "news", "News"
        EVENT = "event", "Event"
        STORY = "story", "Story"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=160, blank=True)
    body = models.TextField()
    kind = models.CharField(
        max_length=24,
        choices=Kind.choices,
        default=Kind.NEWS,
    )
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    event_starts_at = models.DateTimeField(null=True, blank=True)
    event_ends_at = models.DateTimeField(null=True, blank=True)
    event_location = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("-published_at", "-id")

    def __str__(self) -> str:
        return self.title or self.body[:40]


class PostImage(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField()
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("position", "id")

    def __str__(self) -> str:
        return f"Image #{self.position} for post {self.post_id}"


class PostLike(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("post", "user"), name="unique_post_like"),
        ]
        ordering = ("-created_at", "-id")


class PostFavorite(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_favorites",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("post", "user"), name="unique_post_favorite"),
        ]
        ordering = ("-created_at", "-id")


class PostView(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="view_records",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_views",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("post", "user"), name="unique_post_view"),
        ]
        ordering = ("-updated_at", "-id")


class PostComment(TimeStampedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_comments",
    )
    body = models.TextField()

    class Meta:
        ordering = ("created_at", "id")
