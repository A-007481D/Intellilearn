from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.ai.gemini_adapter import GeminiEmbeddingService, GeminiLLMService
from infrastructure.ai.prompt_builder import PromptBuilder
from infrastructure.ai.retriever import VectorRetriever


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get('question')
        document_id = request.data.get('document_id') # optional filter
        
        if not question:
            return Response({"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Embed the question
        embedding_service = GeminiEmbeddingService()
        try:
            # We wrap question in a list because generate_embeddings takes a list
            query_embedding = embedding_service.generate_embeddings([question])[0]
        except Exception:  # noqa: BLE001
            return Response({"error": "Failed to generate embedding"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Retrieve contexts
        doc_ids = [document_id] if document_id else None
        contexts = VectorRetriever.retrieve_context(query_embedding, document_ids=doc_ids, top_k=5)

        # 3. Build prompt
        prompt = PromptBuilder.build_rag_prompt(question, contexts)

        # 4. Generate answer
        llm_service = GeminiLLMService()
        try:
            answer = llm_service.generate_text(prompt)
        except Exception:  # noqa: BLE001
            return Response({"error": "Failed to generate answer"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"answer": answer})
