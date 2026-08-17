from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Sum
from infrastructure.storage.minio_adapter import StorageService
import hashlib

from .models import Document, DocumentStatus
from .serializers import DocumentSerializer


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.role == "ADMIN":
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        title = request.data.get("title", file_obj.name)

        # Determine file size
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(0)
        
        # Check storage quota
        user = request.user
        current_storage = Document.objects.filter(user=user).aggregate(total=Sum('file_size'))['total'] or 0
        if current_storage + size > user.max_storage_bytes:
            return Response({"error": "Storage quota exceeded"}, status=status.HTTP_403_FORBIDDEN)
            
        # Check document count quota
        if Document.objects.filter(user=user).count() >= user.max_documents:
            return Response({"error": "Document count quota exceeded"}, status=status.HTTP_403_FORBIDDEN)
            
        # Check unicity
        file_hash = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        if Document.objects.filter(user=user, file_hash=file_hash).exists():
            return Response({"error": "Document already exists"}, status=status.HTTP_409_CONFLICT)

        # Upload to MinIO
        storage = StorageService()
        try:
            object_name = storage.upload_file(file_obj, file_obj.name)
        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create Document record
        doc = Document.objects.create(
            user=request.user,
            title=title,
            file_path=object_name,
            file_size=size,
            file_hash=file_hash,
            status=DocumentStatus.UPLOADED,
        )

        # Trigger Celery task here
        from .tasks import process_document_task

        process_document_task.delay(doc.id)

        serializer = self.get_serializer(doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "ADMIN":
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        storage = StorageService()
        if instance.file_path:
            storage.delete_file(instance.file_path)
        instance.delete()
