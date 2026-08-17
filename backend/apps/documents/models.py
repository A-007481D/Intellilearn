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
    file_size = models.IntegerField(default=0, help_text="File size in bytes")
    file_hash = models.CharField(
        max_length=64, blank=True, help_text="SHA-256 hash of the file content"
    )
    status = models.CharField(
        max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.UPLOADED
    )
    error_message = models.TextField(
        blank=True, help_text="Set when status=FAILED, describes what went wrong"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
