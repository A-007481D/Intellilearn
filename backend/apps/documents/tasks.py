import time

from celery import shared_task

from .models import Document, DocumentStatus


@shared_task
def process_document_task(document_id):
    """
    Mock task to simulate document processing.
    In Phase 4, this will trigger the real extraction pipeline.
    """
    try:
        doc = Document.objects.get(id=document_id)
        doc.status = DocumentStatus.PROCESSING
        doc.save()

        # Simulate work
        time.sleep(2)

        doc.status = DocumentStatus.READY
        doc.save()
    except Document.DoesNotExist:
        pass
