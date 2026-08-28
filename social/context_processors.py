from .models import Notification, Message


def unread_counts(request):

    if not request.user.is_authenticated:
        return {
            "unread_notifications": 0,
            "unread_messages": 0,
        }

    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    unread_messages = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    return {
        "unread_notifications": unread_notifications,
        "unread_messages": unread_messages,
    }