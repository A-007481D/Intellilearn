from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Document, DocumentStatus
from .tasks import process_document_task

User = get_user_model()


class DocumentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("document_list_create")

    @patch("apps.documents.views.StorageService")
    @patch("apps.documents.tasks.process_document_task.delay")
    def test_document_upload(self, mock_task, mock_storage):
        mock_instance = mock_storage.return_value
        mock_instance.upload_file.return_value = "mocked/path/test.pdf"

        file_content = b"dummy pdf content"
        test_file = SimpleUploadedFile(
            "test.pdf", file_content, content_type="application/pdf"
        )

        data = {"file": test_file, "title": "Test Document"}
        response = self.client.post(self.url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.title, "Test Document")
        self.assertEqual(doc.status, DocumentStatus.UPLOADED)

        mock_instance.upload_file.assert_called_once()
        mock_task.assert_called_once_with(doc.id)


class DocumentTaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", password="password123"
        )
        self.doc = Document.objects.create(
            user=self.user,
            title="Test Doc",
            file_path="mock/path/test.pdf",
            status=DocumentStatus.UPLOADED,
        )

    @patch("apps.documents.tasks.GeminiEmbeddingService")
    @patch("apps.documents.tasks.ChunkingService")
    @patch("apps.documents.tasks.PDFExtractionService")
    @patch("apps.documents.tasks.StorageService")
    def test_process_document_task_success(
        self, mock_storage, mock_pdf, mock_chunk, mock_gemini
    ):
        # Mock Storage
        mock_storage_inst = mock_storage.return_value
        mock_response = MagicMock()
        mock_response.read.return_value = b"pdf data"
        mock_storage_inst.get_file_stream.return_value = mock_response

        # Mock PDF Extractor
        mock_pdf.extract_text.return_value = "Extracted text content."

        # Mock Chunker
        mock_chunk_inst = mock_chunk.return_value
        mock_chunk_inst.chunk_text.return_value = ["Extracted", "text content."]

        # Mock Embeddings
        mock_gemini_inst = mock_gemini.return_value
        mock_gemini_inst.generate_embeddings.return_value = [[0.1] * 768, [0.2] * 768]

        # Run task
        result = process_document_task(self.doc.id)

        self.assertEqual(result, "Success")
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.READY)

        # Verify chunks created
        self.assertEqual(self.doc.chunks.count(), 2)
        chunks = self.doc.chunks.all()
        self.assertEqual(chunks[0].content, "Extracted")
        self.assertEqual(len(chunks[0].embedding), 768)
