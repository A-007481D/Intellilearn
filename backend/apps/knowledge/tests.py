import unittest
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase

from apps.documents.models import Document, DocumentStatus
from apps.knowledge.models import DocumentChunk
from infrastructure.ai.gemini_adapter import GeminiLLMService
from infrastructure.ai.prompt_builder import PromptBuilder
from infrastructure.ai.retriever import VectorRetriever

User = get_user_model()


class RetrieverTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="retriever@test.com", password="foo")
        self.doc = Document.objects.create(
            user=self.user,
            title="Test Doc",
            file_path="mock/path.pdf",
            status=DocumentStatus.READY,
        )
        # Create some chunks with dummy embeddings
        # VectorField accepts lists of floats
        DocumentChunk.objects.create(
            document=self.doc, content="apple", embedding=[1.0] + [0.0] * 767
        )
        DocumentChunk.objects.create(
            document=self.doc, content="banana", embedding=[0.0, 1.0] + [0.0] * 766
        )
        DocumentChunk.objects.create(
            document=self.doc, content="cherry", embedding=[0.0, 0.0, 1.0] + [0.0] * 765
        )

    @unittest.skipIf(connection.vendor != "postgresql", "pgvector requires PostgreSQL")
    def test_retrieve_context(self):
        # Query closer to the first chunk (apple)
        query_embedding = [0.9] + [0.0] * 767
        results = VectorRetriever.retrieve_context(query_embedding, top_k=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "apple")

    @unittest.skipIf(connection.vendor != "postgresql", "pgvector requires PostgreSQL")
    def test_retrieve_context_with_filter(self):
        # Query closer to banana
        query_embedding = [0.0, 0.9] + [0.0] * 766

        # Test filtering by a doc ID that doesn't exist
        empty_results = VectorRetriever.retrieve_context(
            query_embedding, document_ids=[999]
        )
        self.assertEqual(len(empty_results), 0)

        # Test filtering by the correct doc ID
        results = VectorRetriever.retrieve_context(
            query_embedding, document_ids=[self.doc.id], top_k=2
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].content, "banana")


class ContextMock:
    def __init__(self, content):
        self.content = content


class BuilderAndLLMTests(TestCase):
    def test_prompt_builder(self):
        c1 = ContextMock("The mitochondria is the powerhouse of the cell.")
        c2 = ContextMock("Photosynthesis occurs in chloroplasts.")

        prompt = PromptBuilder.build_rag_prompt("What is a cell powerhouse?", [c1, c2])
        self.assertIn("The mitochondria is the powerhouse of the cell.", prompt)
        self.assertIn("Photosynthesis occurs in chloroplasts.", prompt)
        self.assertIn("What is a cell powerhouse?", prompt)
        self.assertIn("strictly on the provided context", prompt)

    @patch("infrastructure.ai.gemini_adapter.genai.Client")
    def test_gemini_llm_service(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_response = MagicMock()
        mock_response.text = "Mocked answer"
        mock_client.models.generate_content.return_value = mock_response

        service = GeminiLLMService()
        response_text = service.generate_text("Test prompt")

        self.assertEqual(response_text, "Mocked answer")
        mock_client.models.generate_content.assert_called_once()
