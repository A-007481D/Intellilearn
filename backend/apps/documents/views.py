import hashlib

from django.db.models import Sum
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.storage.minio_adapter import StorageService

from .models import Document, DocumentStatus
from .serializers import DocumentSerializer


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Document.objects.all().order_by('-uploaded_at')
        return Document.objects.filter(user=user).order_by('-uploaded_at')

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        if not file_obj.name.lower().endswith('.pdf'):
            return Response({'error': 'Only PDF files are allowed'}, status=status.HTTP_400_BAD_REQUEST)

        title = request.data.get('title', file_obj.name)

        # Determine file size
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(0)

        # Validate size <= 50MB
        if size > 50 * 1024 * 1024:
            return Response({'error': 'File exceeds 50MB limit'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Check storage quota
        current_storage = Document.objects.filter(user=user).aggregate(total=Sum('file_size'))['total'] or 0
        if current_storage + size > user.max_storage_bytes:
            return Response({'error': 'Storage quota exceeded'}, status=status.HTTP_403_FORBIDDEN)

        # Check document count quota
        if Document.objects.filter(user=user).count() >= user.max_documents:
            return Response({'error': 'Document count quota exceeded'}, status=status.HTTP_403_FORBIDDEN)

        # Check unicity
        file_hash = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        if Document.objects.filter(user=user, file_hash=file_hash).exists():
            return Response({'error': 'This document has already been uploaded'}, status=status.HTTP_409_CONFLICT)

        # Upload to MinIO
        storage = StorageService()
        try:
            object_name = storage.upload_file(file_obj, file_obj.name)
        except Exception as e:  # noqa: BLE001
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        doc = Document.objects.create(
            user=user,
            title=title,
            file_path=object_name,
            file_size=size,
            file_hash=file_hash,
            status=DocumentStatus.UPLOADED,
        )

        from .tasks import process_document_task
        process_document_task.delay(doc.id)

        serializer = self.get_serializer(doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Document.objects.all()
        return Document.objects.filter(user=user)

    def update(self, request, *args, **kwargs):
        # Only allow renaming (title field)
        instance = self.get_object()
        title = request.data.get('title')
        if not title:
            return Response({'error': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)
        instance.title = title
        instance.save(update_fields=['title'])
        return Response(self.get_serializer(instance).data)

    def perform_destroy(self, instance):
        # Physical delete from MinIO
        storage = StorageService()
        if instance.file_path:
            storage.delete_file(instance.file_path)
        # Chunks will cascade delete (and vectors with them)
        instance.delete()


class DocumentReprocessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        if doc.status == DocumentStatus.PROCESSING:
            return Response({'error': 'Document is already being processed'}, status=status.HTTP_400_BAD_REQUEST)

        # Delete existing chunks
        doc.chunks.all().delete()
        doc.status = DocumentStatus.UPLOADED
        doc.save(update_fields=['status'])

        from .tasks import process_document_task
        process_document_task.delay(doc.id)

        return Response({'status': 'Reprocessing started', 'document_id': doc.id})


class DocumentPresignedUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

        storage = StorageService()
        url = storage.get_file_url(doc.file_path)
        return Response({'url': url, 'document_id': doc.id})
