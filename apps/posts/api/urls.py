from django.urls import path

from .views import (
    PostCommentDetailView,
    PostCommentListCreateView,
    PostDetailView,
    PostFavoriteView,
    PostLikeView,
    PostListCreateView,
)

urlpatterns = [
    path("posts", PostListCreateView.as_view(), name="post-list"),
    path("posts/<int:post_id>", PostDetailView.as_view(), name="post-detail"),
    path("posts/<int:post_id>/like", PostLikeView.as_view(), name="post-like"),
    path("posts/<int:post_id>/favorite", PostFavoriteView.as_view(), name="post-favorite"),
    path("posts/<int:post_id>/comments", PostCommentListCreateView.as_view(), name="post-comments"),
    path(
        "posts/<int:post_id>/comments/<int:comment_id>",
        PostCommentDetailView.as_view(),
        name="post-comment-detail",
    ),
]
