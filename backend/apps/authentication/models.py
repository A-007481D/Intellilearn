from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class Role(models.TextChoices):
    LEARNER = "LEARNER", _("Learner")
    ADMIN = "ADMIN", _("Admin")


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.LEARNER,
    )
    max_documents = models.IntegerField(default=50)
    max_storage_bytes = models.BigIntegerField(default=500 * 1024 * 1024)  # 500 MB

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class QuotaChangeLog(models.Model):
    admin_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="quota_changes_made"
    )
    target_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quota_changes_received"
    )
    old_max_documents = models.IntegerField(default=0)
    new_max_documents = models.IntegerField(default=0)
    old_max_storage_bytes = models.BigIntegerField(default=0)
    new_max_storage_bytes = models.BigIntegerField(default=0)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin_user} → {self.target_user} at {self.timestamp}"


class NotificationLog(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    sender = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='sent_notifications'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_notifications'
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} → {self.recipient.email} [{self.status}]"
