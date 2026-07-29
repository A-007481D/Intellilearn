from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class DocumentStatus(models.TextChoices):
    UPLOADED = "UPLOADED", "Uploaded"
    PROCESSING = "PROCESSING", "Processing"
    READY = "READY", "Ready"
    FAILED = "FAILED", "Failed"


class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, help_text="MinIO object path")
    status = models.CharField(
        max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.UPLOADED
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
