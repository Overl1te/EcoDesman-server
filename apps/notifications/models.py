from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Kind(models.TextChoices):
        POST_LIKED = "post_liked", "Post liked"
        POST_COMMENTED = "post_commented", "Post commented"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="triggered_notifications",
    )
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    comment = models.ForeignKey(
        "posts.PostComment",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=160)
    body = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        return f"{self.kind} -> {self.recipient_id}"

