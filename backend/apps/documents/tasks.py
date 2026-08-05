import io

from celery import shared_task
from django.db import transaction

from apps.knowledge.models import DocumentChunk
from infrastructure.ai.chunking_adapter import ChunkingService
from infrastructure.ai.gemini_adapter import GeminiEmbeddingService
from infrastructure.ai.pdf_adapter import PDFExtractionService
from infrastructure.storage.minio_adapter import StorageService

from .models import Document, DocumentStatus


@shared_task
def process_document_task(document_id):
    try:
        doc = Document.objects.get(id=document_id)
        doc.status = DocumentStatus.PROCESSING
        doc.save()

        # 1. Download file stream
        storage = StorageService()
        response = storage.get_file_stream(doc.file_path)
        file_stream = io.BytesIO(response.read())
        response.close()
        response.release_conn()

        # 2. Extract Text
        text = PDFExtractionService.extract_text(file_stream)

        if not text.strip():
            doc.status = DocumentStatus.FAILED
            doc.save()
            return "Failed: No text extracted"

        # 3. Chunk Text
        chunker = ChunkingService()
        chunks = chunker.chunk_text(text)

        # 4. Generate Embeddings
        embedder = GeminiEmbeddingService()
        embeddings = embedder.generate_embeddings(chunks)

        # 5. Save Chunks
        with transaction.atomic():
            for chunk_text, embedding in zip(chunks, embeddings):
                DocumentChunk.objects.create(
                    document=doc, content=chunk_text, embedding=embedding
                )

        doc.status = DocumentStatus.READY
        doc.save()
        return "Success"

    except Exception as e:  # noqa: BLE001
        Document.objects.filter(id=document_id).update(status=DocumentStatus.FAILED)
        return f"Failed: {e!s}"
