from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Post, PostComment
from ..selectors import get_post, list_comments, list_posts
from ..services import (
    add_comment,
    can_edit_comment,
    can_edit_post,
    create_post,
    favorite_post,
    increment_post_view,
    like_post,
    unfavorite_post,
    unlike_post,
    update_post,
)
from .pagination import PostPagination
from .serializers import (
    CommentWriteSerializer,
    FavoriteStateSerializer,
    LikeStateSerializer,
    PostCommentSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
)


def _parse_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class PostListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        author_id = request.query_params.get("author_id")
        search = request.query_params.get("search")
        kind = request.query_params.get("kind")
        ordering = request.query_params.get("ordering")
        event_scope = request.query_params.get("event_scope")
        try:
            author_id_value = int(author_id) if author_id else None
        except ValueError:
            return Response(
                {"detail": "author_id must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = list_posts(
            viewer=request.user,
            author_id=author_id_value,
            search=search,
            kind=kind,
            ordering=ordering,
            has_images=_parse_bool(request.query_params.get("has_images")),
            favorites_only=_parse_bool(request.query_params.get("favorites_only")),
            event_scope=event_scope,
        )
        paginator = PostPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PostListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PostWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = create_post(author=request.user, validated_data=serializer.validated_data)
        post = get_object_or_404(get_post(post.id, viewer=request.user))
        return Response(
            PostDetailSerializer(post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, post_id: int):
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        increment_post_view(post, viewer=request.user)
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        return Response(PostDetailSerializer(post, context={"request": request}).data)

    def patch(self, request, post_id: int):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        post = get_object_or_404(Post, id=post_id)
        if not can_edit_post(request.user, post):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = PostWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_post(post=post, validated_data=serializer.validated_data)
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        return Response(PostDetailSerializer(post, context={"request": request}).data)

    def delete(self, request, post_id: int):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        post = get_object_or_404(Post, id=post_id)
        if not can_edit_post(request.user, post):
            return Response(status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id, is_published=True)
        like_post(post=post, user=request.user)
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        return Response(
            LikeStateSerializer(
                {
                    "likes_count": post.likes_count,
                    "is_liked": True,
                }
            ).data
        )

    def delete(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id, is_published=True)
        unlike_post(post=post, user=request.user)
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        return Response(
            LikeStateSerializer(
                {
                    "likes_count": post.likes_count,
                    "is_liked": False,
                }
            ).data
        )


class PostFavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id, is_published=True)
        favorite_post(post=post, user=request.user)
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        return Response(
            FavoriteStateSerializer(
                {
                    "favorites_count": post.favorites_count,
                    "is_favorited": True,
                }
            ).data
        )

    def delete(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id, is_published=True)
        unfavorite_post(post=post, user=request.user)
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        return Response(
            FavoriteStateSerializer(
                {
                    "favorites_count": post.favorites_count,
                    "is_favorited": False,
                }
            ).data
        )


class PostCommentListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, post_id: int):
        get_object_or_404(get_post(post_id, viewer=request.user))
        comments = list_comments(post_id)
        serializer = PostCommentSerializer(comments, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, post_id: int):
        post = get_object_or_404(get_post(post_id, viewer=request.user))
        serializer = CommentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = add_comment(
            post=post,
            author=request.user,
            body=serializer.validated_data["body"],
        )
        return Response(
            PostCommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PostCommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, post_id: int, comment_id: int):
        comment = get_object_or_404(PostComment, id=comment_id, post_id=post_id)
        if not can_edit_comment(request.user, comment):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = CommentWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "body" in serializer.validated_data:
            comment.body = serializer.validated_data["body"]
            comment.save(update_fields=["body", "updated_at"])
        return Response(PostCommentSerializer(comment, context={"request": request}).data)

    def delete(self, request, post_id: int, comment_id: int):
        comment = get_object_or_404(PostComment, id=comment_id, post_id=post_id)
        if not can_edit_comment(request.user, comment):
            return Response(status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
