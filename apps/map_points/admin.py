from django.contrib import admin

from .models import MapPoint, MapPointCategory, MapPointImage, MapPointReview


class MapPointImageInline(admin.TabularInline):
    model = MapPointImage
    extra = 0


class MapPointReviewInline(admin.TabularInline):
    model = MapPointReview
    extra = 0


@admin.register(MapPointCategory)
class MapPointCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "sort_order")
    search_fields = ("title", "slug")
    ordering = ("sort_order", "title")


@admin.register(MapPoint)
class MapPointAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "latitude",
        "longitude",
        "is_active",
        "sort_order",
    )
    list_filter = ("is_active", "categories")
    search_fields = ("title", "slug", "short_description", "address")
    filter_horizontal = ("categories",)
    inlines = [MapPointImageInline, MapPointReviewInline]
    ordering = ("sort_order", "title")
