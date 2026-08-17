import io
import re

from celery import shared_task
from django.db import transaction

from apps.knowledge.models import DocumentChunk
from infrastructure.ai.chunking_adapter import ChunkingService
from infrastructure.ai.gemini_adapter import GeminiEmbeddingService
from infrastructure.ai.pdf_adapter import PDFExtractionService
from infrastructure.storage.minio_adapter import StorageService

from .models import Document, DocumentStatus


def _parse_page_number(chunk_text):
    """Extract the last [PAGE:N] marker found in a chunk."""
    matches = re.findall(r"\[PAGE:(\d+)\]", chunk_text)
    if matches:
        return int(matches[-1])
    return None


def _clean_chunk(chunk_text):
    """Remove [PAGE:N] markers from chunk content."""
    return re.sub(r"\[PAGE:\d+\]\n?", "", chunk_text).strip()


@shared_task
def process_document_task(document_id):
    try:
        doc = Document.objects.get(id=document_id)
        doc.status = DocumentStatus.PROCESSING
        doc.save()

        # 1. Download file stream from MinIO
        storage = StorageService()
        response = storage.get_file_stream(doc.file_path)
        file_stream = io.BytesIO(response.read())
        response.close()
        response.release_conn()

        # 2. Extract Text (with page count validation)
        try:
            text, _page_count = PDFExtractionService.extract_text(file_stream)
        except ValueError as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            doc.save(update_fields=["status", "error_message"])
            return f"Failed: {e}"

        if not text.strip():
            doc.status = DocumentStatus.FAILED
            doc.error_message = "No readable text could be extracted from this document. It may be a scanned image-only PDF or protected."
            doc.save(update_fields=["status", "error_message"])
            return "Failed: No text extracted"

        # 3. Chunk Text
        chunker = ChunkingService()
        raw_chunks = chunker.chunk_text(text)

        # 4. Generate Embeddings
        embedder = GeminiEmbeddingService()
        embeddings = embedder.generate_embeddings(raw_chunks)

        # 5. Save Chunks with page numbers
        with transaction.atomic():
            for chunk_text, embedding in zip(raw_chunks, embeddings):
                page_num = _parse_page_number(chunk_text)
                clean_content = _clean_chunk(chunk_text)
                DocumentChunk.objects.create(
                    document=doc,
                    content=clean_content,
                    embedding=embedding,
                    page_number=page_num,
                )

        doc.status = DocumentStatus.READY
        doc.error_message = ""
        doc.save(update_fields=["status", "error_message"])
        return "Success"

    except Exception as e:  # noqa: BLE001
        Document.objects.filter(id=document_id).update(
            status=DocumentStatus.FAILED,
            error_message=str(e),
        )
        return f"Failed: {e!s}"
