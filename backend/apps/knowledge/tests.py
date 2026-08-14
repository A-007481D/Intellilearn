import unittest
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import Document, DocumentStatus
from apps.knowledge.models import (
    DocumentChunk,
    Question,
    Quiz,
    QuizAttempt,
)
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
        self.id = 1
        self.pk = 1


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


class ChatViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="chat@test.com", password="foo")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("chat")

    @patch("apps.knowledge.views.GeminiLLMService")
    @patch("apps.knowledge.views.VectorRetriever")
    @patch("apps.knowledge.views.GeminiEmbeddingService")
    def test_chat_success(self, mock_embedding, mock_retriever, mock_llm):
        doc = Document.objects.create(
            user=self.user,
            title="Test",
            file_path="test.pdf",
            status=DocumentStatus.READY,
        )
        chunk = DocumentChunk.objects.create(
            document=doc, content="Context one.", embedding=[0.0] * 768
        )

        # Mock embeddings
        mock_embedding_inst = mock_embedding.return_value
        mock_embedding_inst.generate_embeddings.return_value = [[0.1] * 768]

        # Mock retriever
        mock_retriever.retrieve_context.return_value = [chunk]

        # Mock LLM
        mock_llm_inst = mock_llm.return_value
        mock_llm_inst.generate_text.return_value = "This is the answer."

        response = self.client.post(
            self.url, {"question": "What is this?"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["answer"], "This is the answer.")

        mock_embedding_inst.generate_embeddings.assert_called_once_with(
            ["What is this?"]
        )
        mock_retriever.retrieve_context.assert_called_once()
        mock_llm_inst.generate_text.assert_called_once()


class QuizTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="quiz@test.com", password="foo")
        self.client.force_authenticate(user=self.user)

        self.doc = Document.objects.create(
            user=self.user,
            title="Test",
            file_path="test.pdf",
            status=DocumentStatus.READY,
        )
        self.chunk = DocumentChunk.objects.create(
            document=self.doc, content="Context one.", embedding=[0.0] * 768
        )

    @patch("apps.knowledge.views.GeminiLLMService")
    def test_quiz_generate(self, mock_llm):
        mock_llm_inst = mock_llm.return_value
        mock_llm_inst.generate_text.return_value = """[
            {
                "text": "What is the capital of France?",
                "options": ["Paris", "London", "Berlin", "Rome"],
                "correct_answer": "Paris",
                "explanation": "Paris is the capital of France."
            }
        ]"""

        url = reverse("quiz-generate")
        response = self.client.post(
            url,
            {"document_id": self.doc.id, "difficulty": "easy", "num_questions": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quiz.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)

    def test_quiz_submit(self):
        quiz = Quiz.objects.create(user=self.user, document=self.doc, title="Test Quiz")
        q1 = Question.objects.create(
            quiz=quiz,
            text="Q1",
            options=["A", "B"],
            correct_answer="A",
            explanation="exp 1",
        )
        q2 = Question.objects.create(
            quiz=quiz,
            text="Q2",
            options=["C", "D"],
            correct_answer="C",
            explanation="exp 2",
        )

        url = reverse("quiz-submit", args=[quiz.id])
        data = {
            "answers": [
                {"question_id": q1.id, "answer": "A"},
                {"question_id": q2.id, "answer": "D"},  # Incorrect
            ]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["score"], 1)
        self.assertEqual(QuizAttempt.objects.count(), 1)
