from django.db.models import Q
from django.utils import timezone

from .models import User


def get_user_by_identifier(identifier: str) -> User | None:
    normalized = identifier.strip()
    if not normalized:
        return None

    return (
        User.objects.filter(
            Q(email__iexact=normalized)
            | Q(phone__iexact=normalized)
            | Q(username__iexact=normalized)
        )
        .order_by("id")
        .first()
    )


def authenticate_user(identifier: str, password: str) -> User | None:
    user = get_user_by_identifier(identifier)
    if not user or not user.is_active:
        return None

    if not user.check_password(password):
        return None

    return user


def can_manage_posts(user) -> bool:
    return bool(user and user.is_authenticated and user.is_post_manager)


def can_administrate(user) -> bool:
    return bool(user and user.is_authenticated and user.is_admin_role)


def issue_warning(target: User) -> User:
    target.warning_count += 1
    if target.warning_count >= 5:
        target.is_active = False
        target.banned_at = timezone.now()
    target.save(update_fields=["warning_count", "is_active", "banned_at"])
    return target


def ban_user(target: User) -> User:
    target.is_active = False
    target.banned_at = timezone.now()
    target.save(update_fields=["is_active", "banned_at"])
    return target


def unban_user(target: User) -> User:
    target.is_active = True
    target.banned_at = None
    target.warning_count = 0
    target.save(update_fields=["is_active", "banned_at", "warning_count"])
    return target


def update_user_role(target: User, role: str) -> User:
    target.role = role
    target.save(update_fields=["role"])
    return target
