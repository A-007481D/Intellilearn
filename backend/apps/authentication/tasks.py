from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_notification_task(subject, message, recipient_list):
    if not recipient_list:
        return
        
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@intellilearn.com',
        recipient_list,
        fail_silently=True,
    )
