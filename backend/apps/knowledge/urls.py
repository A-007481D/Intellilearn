from django.urls import path

from .views import (
    ChatView,
    ConversationDetailView,
    ConversationListView,
    QuizDetailView,
    QuizGenerateView,
    QuizSubmitView,
)

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path(
        "conversations/<int:pk>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path("quizzes/generate/", QuizGenerateView.as_view(), name="quiz-generate"),
    path("quizzes/<int:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
    path("quizzes/<int:pk>/submit/", QuizSubmitView.as_view(), name="quiz-submit"),
]
