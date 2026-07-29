from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ("id", "title", "status", "uploaded_at", "updated_at", "url")
        read_only_fields = ("status", "uploaded_at", "updated_at")

    def get_url(self, obj):
        from infrastructure.storage.minio_adapter import StorageService

        try:
            return StorageService().get_file_url(obj.file_path)
        except Exception:  # noqa: BLE001
            return None
