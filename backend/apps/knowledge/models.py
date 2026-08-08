from django.db import models
from pgvector.django import VectorField
from django.conf import settings

from apps.documents.models import Document


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="chunks"
    )
    page_number = models.IntegerField(null=True, blank=True)
    content = models.TextField()
    # Gemini text-embedding-004 has 768 dimensions
    embedding = VectorField(dimensions=768)

    def __str__(self):
        return f"{self.document.title} - Chunk {self.id}"

class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} - {self.user.email}"

class Message(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        AI = 'ai', 'AI'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    citations = models.ManyToManyField(DocumentChunk, blank=True, related_name='cited_in_messages')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:20]}"
