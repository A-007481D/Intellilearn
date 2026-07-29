from django.conf import settings
from google import genai


class GeminiEmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts."""
        result = self.client.models.embed_content(
            model="text-embedding-004", contents=texts
        )
        return [res.values for res in result.embeddings]
