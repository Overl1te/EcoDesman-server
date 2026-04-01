from .models import Notification


def create_notification(
    *,
    recipient,
    actor,
    kind: str,
    title: str,
    body: str,
    post=None,
    comment=None,
) -> Notification | None:
    if not recipient or not actor or recipient.id == actor.id:
        return None

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        kind=kind,
        title=title,
        body=body,
        post=post,
        comment=comment,
    )

