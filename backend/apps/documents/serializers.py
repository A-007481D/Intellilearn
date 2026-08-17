from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    file_size_bytes = serializers.IntegerField(source="file_size", read_only=True)
    created_at = serializers.DateTimeField(source="uploaded_at", read_only=True)

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "status",
            "created_at",
            "updated_at",
            "url",
            "file_size_bytes",
            "error_message",
        )
        read_only_fields = ("status", "created_at", "updated_at", "error_message")

    def get_url(self, obj):
        from infrastructure.storage.minio_adapter import StorageService

        try:
            return StorageService().get_file_url(obj.file_path)
        except Exception:  # noqa: BLE001
            return None
