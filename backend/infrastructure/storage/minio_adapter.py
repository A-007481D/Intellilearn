import os
import uuid

from django.conf import settings
from minio import Minio


class StorageService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME

        # Ensure bucket exists
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_file(self, file_obj, original_filename):
        """Uploads a file to MinIO and returns the object name."""
        ext = os.path.splitext(original_filename)[1]
        object_name = f"documents/{uuid.uuid4()}{ext}"

        # Determine file size
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(0)

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=file_obj,
            length=size,
        )

        return object_name

    def get_file_url(self, object_name, expires=None):
        from datetime import timedelta
        if expires is None:
            expires = timedelta(hours=1)
        return self.client.presigned_get_object(
            self.bucket_name, object_name, expires=expires
        )

    def get_file_stream(self, object_name):
        return self.client.get_object(self.bucket_name, object_name)
