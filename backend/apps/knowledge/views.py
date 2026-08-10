from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.ai.gemini_adapter import GeminiEmbeddingService, GeminiLLMService
from infrastructure.ai.prompt_builder import PromptBuilder
from infrastructure.ai.retriever import VectorRetriever

from .models import Conversation, Message
from .serializers import ConversationSerializer


class ConversationListView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by(
            "-updated_at"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ConversationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question")
        document_id = request.data.get("document_id")
        conversation_id = request.data.get("conversation_id")

        if not question:
            return Response(
                {"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Handle conversation
        conversation = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id, user=request.user
                )
            except Conversation.DoesNotExist:
                return Response(
                    {"error": "Conversation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            conversation = Conversation.objects.create(
                user=request.user, document_id=document_id, title=question[:50]
            )

        # Get last 5 messages for history context
        history_qs = conversation.messages.order_by("-created_at")[:5]
        history = list(reversed(history_qs))

        embedding_service = GeminiEmbeddingService()
        try:
            query_embedding = embedding_service.generate_embeddings([question])[0]
        except Exception:  # noqa: BLE001
            return Response(
                {"error": "Failed to generate embedding"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        doc_ids = [document_id] if document_id else None
        contexts = VectorRetriever.retrieve_context(
            query_embedding, document_ids=doc_ids, top_k=5
        )

        prompt = PromptBuilder.build_rag_prompt(question, contexts, history=history)

        llm_service = GeminiLLMService()
        try:
            answer = llm_service.generate_text(prompt)
        except Exception:  # noqa: BLE001
            return Response(
                {"error": "Failed to generate answer"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Save messages to history
        Message.objects.create(
            conversation=conversation, role=Message.Role.USER, content=question
        )
        ai_msg = Message.objects.create(
            conversation=conversation, role=Message.Role.AI, content=answer
        )
        ai_msg.citations.set(contexts)

        return Response(
            {
                "conversation_id": conversation.id,
                "answer": answer,
                "citations": [c.id for c in contexts],
            }
        )
