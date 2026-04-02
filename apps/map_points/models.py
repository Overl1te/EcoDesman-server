from django.db import models

from apps.common.models import TimeStampedModel


class MapPointCategory(TimeStampedModel):
    slug = models.SlugField(max_length=64, unique=True)
    title = models.CharField(max_length=80)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "title", "id")
        verbose_name = "Map point category"
        verbose_name_plural = "Map point categories"

    def __str__(self) -> str:
        return self.title


class MapPoint(TimeStampedModel):
    slug = models.SlugField(max_length=64, unique=True)
    title = models.CharField(max_length=120)
    short_description = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=220, blank=True)
    working_hours = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(
        MapPointCategory,
        related_name="points",
        blank=True,
    )

    class Meta:
        ordering = ("sort_order", "title", "id")

    def __str__(self) -> str:
        return self.title


class MapPointImage(TimeStampedModel):
    point = models.ForeignKey(
        MapPoint,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField()
    caption = models.CharField(max_length=140, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("position", "id")

    def __str__(self) -> str:
        return f"Image #{self.position} for point {self.point_id}"


class MapPointReview(TimeStampedModel):
    point = models.ForeignKey(
        MapPoint,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    body = models.TextField()

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        return f"Review by {self.author_name} for {self.point_id}"
