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
    max_storage_bytes = models.BigIntegerField(default=500 * 1024 * 1024)  # 500 MB default

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class QuotaChangeLog(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="quota_changes_made")
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quota_changes_received")
    old_max_documents = models.IntegerField()
    new_max_documents = models.IntegerField()
    old_max_storage_bytes = models.BigIntegerField()
    new_max_storage_bytes = models.BigIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin_user} changed quotas for {self.target_user} at {self.timestamp}"
