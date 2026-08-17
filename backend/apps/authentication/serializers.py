from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "password", "role")

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data.get("role", "LEARNER"),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()
    storage_used = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "role",
            "max_documents",
            "max_storage_bytes",
            "document_count",
            "storage_used",
        )

    def get_document_count(self, obj):
        from apps.documents.models import Document

        return Document.objects.filter(user=obj).count()

    def get_storage_used(self, obj):
        from django.db.models import Sum

        from apps.documents.models import Document

        return (
            Document.objects.filter(user=obj).aggregate(total=Sum("file_size"))["total"]
            or 0
        )
