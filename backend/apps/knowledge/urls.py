from django.urls import path

from .views import (
    AnalyticsView,
    ChatStreamView,
    ChatView,
    ConversationDetailView,
    ConversationListView,
    DocumentSummaryView,
    QuizAttemptDetailView,
    QuizDetailView,
    QuizGenerateView,
    QuizListView,
    QuizSubmitView,
)

urlpatterns = [
    # Chat (JSON response)
    path("chat/", ChatView.as_view(), name="chat"),
    # Chat SSE streaming
    path("chat/stream/", ChatStreamView.as_view(), name="chat-stream"),
    # Conversations
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path(
        "conversations/<int:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    # Quizzes
    path("quizzes/", QuizListView.as_view(), name="quiz-list"),
    path("quizzes/generate/", QuizGenerateView.as_view(), name="quiz-generate"),
    path("quizzes/<int:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
    path("quizzes/<int:pk>/submit/", QuizSubmitView.as_view(), name="quiz-submit"),
    path(
        "quizzes/attempts/<int:pk>/",
        QuizAttemptDetailView.as_view(),
        name="quiz-attempt-detail",
    ),
    # Analytics
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    # Summary/Fiche
    path(
        "documents/<int:pk>/summary/",
        DocumentSummaryView.as_view(),
        name="document-summary",
    ),
]
