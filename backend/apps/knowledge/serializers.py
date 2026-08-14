from rest_framework import serializers

from .models import Conversation, Message, Question, QuestionResponse, Quiz, QuizAttempt


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


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text", "options"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "user",
            "document",
            "title",
            "difficulty",
            "created_at",
            "questions",
        ]
        read_only_fields = ["user", "questions"]


class QuestionResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionResponse
        fields = ["question", "user_answer", "is_correct"]
        read_only_fields = ["is_correct"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    responses = QuestionResponseSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = ["id", "user", "quiz", "score", "created_at", "responses"]
        read_only_fields = ["user", "score", "responses"]
