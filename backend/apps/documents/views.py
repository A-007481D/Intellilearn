from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from infrastructure.storage.minio_adapter import StorageService

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
