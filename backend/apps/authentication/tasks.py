from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_bulk_notification_task(subject, message, recipient_email, log_id):
    from .models import NotificationLog

    try:
        send_mail(
            subject,
            message,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@intellilearn.com"),
            [recipient_email],
            fail_silently=False,
        )
        NotificationLog.objects.filter(id=log_id).update(status="SENT")
    except Exception as e:  # noqa: BLE001
        NotificationLog.objects.filter(id=log_id).update(
            status="FAILED", error_message=str(e)
        )
