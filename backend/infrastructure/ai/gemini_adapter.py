from django.conf import settings
from google import genai


class GeminiEmbeddingService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_embeddings(self, texts):
        """Generate embeddings for a list of texts."""
        result = self.client.models.embed_content(
            model="gemini-embedding-2", contents=texts
        )
        return [res.values for res in result.embeddings]


class GeminiLLMService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_text(self, prompt):
        """Generates text from a given prompt using Gemini."""
        response = self.client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return response.text
