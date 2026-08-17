from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from apps.documents.models import Document


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="chunks"
    )
    page_number = models.IntegerField(null=True, blank=True)
    content = models.TextField()
    # Gemini text-embedding-004 has 768 dimensions
    embedding = VectorField(dimensions=768)

    def __str__(self):
        return f"{self.document.title} - Chunk {self.id}"


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations"
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id} - {self.user.email}"


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        AI = "ai", "AI"

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    citations = models.ManyToManyField(
        DocumentChunk, blank=True, related_name="cited_in_messages"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:20]}"


class Quiz(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes"
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quizzes",
    )
    title = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=50, default="medium")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MCQ = "mcq", "Multiple Choice"
        TRUE_FALSE = "true_false", "True / False"
        OPEN = "open", "Open Question"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )
    text = models.TextField()
    options = models.JSONField(
        help_text="List of possible answers (empty for open questions)",
        default=list,
        blank=True,
    )
    correct_answer = models.CharField(max_length=512)
    concept = models.CharField(
        max_length=255, blank=True, help_text="Core concept being tested"
    )
    explanation = models.TextField(blank=True)
    # Link to source document chunks so results can cite origins
    source_chunks = models.ManyToManyField(
        DocumentChunk, blank=True, related_name="sourced_questions"
    )

    def __str__(self):
        return self.text[:50]


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.quiz.title} ({self.score})"


class QuestionResponse(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="responses"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, help_text="LLM feedback for open answers")

    def __str__(self):
        return f"{self.attempt.id} - {self.question.id}: {self.is_correct}"
