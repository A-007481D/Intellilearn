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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
