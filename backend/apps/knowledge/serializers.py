from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    citations = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ["id", "role", "content", "citations", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "user",
            "document",
            "title",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = ["user", "messages"]
