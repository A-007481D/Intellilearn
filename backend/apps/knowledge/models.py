from django.db import models
from pgvector.django import VectorField

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
