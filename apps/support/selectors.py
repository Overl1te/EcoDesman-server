import re

from django.db.models import QuerySet

from .models import ContentReport, SupportThread

SUPPORT_KNOWLEDGE_BASE = [
    {
        "id": "login-trouble",
        "category": "Аккаунт",
        "title": "Не получается войти в аккаунт",
        "answer": (
            "Проверьте логин или почту без лишних пробелов, попробуйте сбросить пароль "
            "и убедитесь, что аккаунт не был заблокирован после предупреждений."
        ),
        "keywords": [
            "войти",
            "логин",
            "пароль",
            "аккаунт",
            "авторизация",
            "sign in",
        ],
        "is_featured": True,
    },
    {
        "id": "post-or-comment-missing",
        "category": "Контент",
        "title": "Пост или комментарий пропал",
        "answer": (
            "Сначала проверьте профиль и черновики. Если запись удалена или скрыта после жалобы, "
            "откройте чат с поддержкой: там будет история обращения и ответ специалиста."
        ),
        "keywords": [
            "пост",
            "комментарий",
            "пропал",
            "удален",
            "жалоба",
            "скрыт",
        ],
        "is_featured": True,
    },
    {
        "id": "map-review-issue",
        "category": "Карта",
        "title": "Проблема с точкой на карте или отзывом",
        "answer": (
            "Если точка карты не открывается, отзыв не публикуется или фото не загружается, "
            "приложите ссылку на точку, текст ошибки и скриншот. Это сильно ускорит проверку."
        ),
        "keywords": [
            "карта",
            "точка",
            "отзыв",
            "review",
            "map",
            "фото",
        ],
        "is_featured": True,
    },
    {
        "id": "notifications-delay",
        "category": "Уведомления",
        "title": "Не приходят уведомления",
        "answer": (
            "Обновите экран уведомлений, проверьте интернет и разрешения устройства. "
            "Если уведомления о поддержке или жалобах все равно не приходят, создайте обращение."
        ),
        "keywords": [
            "уведомления",
            "notification",
            "не приходят",
            "не вижу",
        ],
        "is_featured": False,
    },
    {
        "id": "mobile-profile-help",
        "category": "Мобильное приложение",
        "title": "Где на мобильном найти помощь",
        "answer": (
            "Раздел «Справка и помощь» находится в профиле. Там доступны FAQ, мини-бот, "
            "история обращений и статусы жалоб."
        ),
        "keywords": [
            "мобильное",
            "профиль",
            "помощь",
            "справка",
            "android",
            "ios",
        ],
        "is_featured": False,
    },
]


def list_support_knowledge() -> dict[str, list[dict]]:
    faq = sorted(
        SUPPORT_KNOWLEDGE_BASE,
        key=lambda item: (not item["is_featured"], item["category"], item["title"]),
    )
    featured = [item for item in faq if item["is_featured"]]
    return {
        "featured": featured,
        "faq": faq,
        "suggested_prompts": [item["title"] for item in featured[:4]],
    }


def tokenize_support_query(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[\w-]+", value.lower(), flags=re.UNICODE)
        if len(token) > 2
    }


def match_support_article(query: str) -> dict | None:
    query_tokens = tokenize_support_query(query)
    if not query_tokens:
        return None

    best_match = None
    best_score = 0
    for article in SUPPORT_KNOWLEDGE_BASE:
        article_tokens = tokenize_support_query(article["title"])
        for keyword in article["keywords"]:
            article_tokens.update(tokenize_support_query(keyword))
        score = len(query_tokens.intersection(article_tokens))
        if score > best_score:
            best_score = score
            best_match = article

    return best_match if best_score > 0 else None


def list_user_threads(user) -> QuerySet[SupportThread]:
    return (
        SupportThread.objects.filter(created_by=user)
        .select_related("created_by", "assigned_to", "linked_report")
    )


def list_team_threads() -> QuerySet[SupportThread]:
    return (
        SupportThread.objects.all()
        .select_related("created_by", "assigned_to", "linked_report")
        .order_by("-unread_for_support_count", "-last_message_at", "-id")
    )


def list_team_reports() -> QuerySet[ContentReport]:
    return (
        ContentReport.objects.all()
        .select_related(
            "reporter",
            "reviewed_by",
            "support_thread",
            "post",
            "comment",
            "review",
        )
        .order_by("-created_at", "-id")
    )
