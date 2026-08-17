import json

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from infrastructure.ai.gemini_adapter import GeminiEmbeddingService, GeminiLLMService
from infrastructure.ai.orchestrator import AgentOrchestrator
from infrastructure.ai.prompt_builder import QuizPromptBuilder
from infrastructure.ai.retriever import VectorRetriever

from .models import Conversation, Message, Question, QuestionResponse, Quiz, QuizAttempt
from .serializers import ConversationSerializer, QuizSerializer


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

    def _generate_quiz_inline(self, request, contexts, document):
        prompt = QuizPromptBuilder.build_quiz_prompt(contexts, "medium", 5)
        llm_service = GeminiLLMService()
        try:
            answer = llm_service.generate_text(prompt)
            answer = (
                answer.removeprefix("```json").removeprefix("```").removesuffix("```")
            )
            questions_data = json.loads(answer.strip())

            quiz = Quiz.objects.create(
                user=request.user,
                document=document,
                title=f"{document.title} Quiz (Auto)",
                difficulty="medium",
            )
            for q_data in questions_data:
                Question.objects.create(
                    quiz=quiz,
                    text=q_data.get("text", ""),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", ""),
                    concept=q_data.get("concept", ""),
                    explanation=q_data.get("explanation", ""),
                )
        except Exception:  # noqa: S110, BLE001
            pass

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

        orchestrator = AgentOrchestrator(contexts)
        intent = orchestrator.classify_intent(question)

        if intent == "QUIZ":
            doc = contexts[0].document if contexts else None
            if doc:
                self._generate_quiz_inline(request, contexts, doc)
            answer = "I have generated a quiz based on your request. You can find it in the Quizzes tab."
        else:
            try:
                answer = orchestrator.answer_question(question, history)
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


class QuizGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        document_id = request.data.get("document_id")
        difficulty = request.data.get("difficulty", "medium")
        num_questions = int(request.data.get("num_questions", 5))

        if not document_id:
            return Response(
                {"error": "document_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document = Document.objects.get(id=document_id, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Let's just grab the first 10 chunks to base the quiz on
        contexts = document.chunks.all()[:10]
        if not contexts:
            return Response(
                {"error": "Document has no processed chunks"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = QuizPromptBuilder.build_quiz_prompt(
            contexts, difficulty, num_questions
        )

        llm_service = GeminiLLMService()
        try:
            answer = llm_service.generate_text(prompt)
            answer = answer.removeprefix("```json")
            answer = answer.removeprefix("```")
            answer = answer.removesuffix("```")

            questions_data = json.loads(answer.strip())
        except Exception:  # noqa: BLE001
            return Response(
                {"error": "Failed to generate quiz"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        quiz = Quiz.objects.create(
            user=request.user,
            document=document,
            title=f"{document.title} Quiz",
            difficulty=difficulty,
        )

        for q_data in questions_data:
            Question.objects.create(
                quiz=quiz,
                text=q_data.get("text", ""),
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer", ""),
                concept=q_data.get("concept", ""),
                explanation=q_data.get("explanation", ""),
            )

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizDetailView(generics.RetrieveAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)


class QuizSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            quiz = Quiz.objects.get(pk=pk, user=request.user)
        except Quiz.DoesNotExist:
            return Response(
                {"error": "Quiz not found"}, status=status.HTTP_404_NOT_FOUND
            )

        answers = request.data.get("answers", [])

        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
        score = 0

        for ans in answers:
            q_id = ans.get("question_id")
            user_ans = ans.get("answer")
            try:
                question = quiz.questions.get(id=q_id)
                is_correct = question.correct_answer == user_ans
                if is_correct:
                    score += 1
                QuestionResponse.objects.create(
                    attempt=attempt,
                    question=question,
                    user_answer=user_ans,
                    is_correct=is_correct,
                )
            except Question.DoesNotExist:
                continue

        attempt.score = score
        attempt.save()

        responses = attempt.responses.all()
        res_data = []
        for r in responses:
            res_data.append(
                {
                    "question_id": r.question.id,
                    "user_answer": r.user_answer,
                    "is_correct": r.is_correct,
                    "correct_answer": r.question.correct_answer,
                    "explanation": r.question.explanation,
                }
            )

        return Response(
            {
                "attempt_id": attempt.id,
                "score": score,
                "total": quiz.questions.count(),
                "results": res_data,
            }
        )


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        total_documents = Document.objects.filter(user=user).count()
        
        # Count user messages across all their conversations
        total_questions_asked = Message.objects.filter(
            conversation__user=user, 
            role=Message.Role.USER
        ).count()
        
        # Quiz stats
        attempts = QuizAttempt.objects.filter(user=user).prefetch_related("quiz__questions")
        total_quizzes_taken = attempts.count()
        
        avg_score = 0
        if total_quizzes_taken > 0:
            avg_score = sum([a.score / max(a.quiz.questions.count(), 1) * 100 for a in attempts]) / total_quizzes_taken
            
        # Concept tracking
        responses = QuestionResponse.objects.filter(attempt__user=user).select_related("question")
        concept_stats = {}
        
        for r in responses:
            concept = r.question.concept
            if not concept:
                continue
            if concept not in concept_stats:
                concept_stats[concept] = {"correct": 0, "total": 0}
            concept_stats[concept]["total"] += 1
            if r.is_correct:
                concept_stats[concept]["correct"] += 1
                
        # Calculate success rate and find weakest
        weakest_concepts = []
        for concept, stats in concept_stats.items():
            rate = (stats["correct"] / stats["total"]) * 100
            weakest_concepts.append({"concept": concept, "success_rate": rate})
            
        weakest_concepts.sort(key=lambda x: x["success_rate"])
        top_weakest = weakest_concepts[:3]
        
        # Progression over time (last 10 attempts)
        recent_attempts = attempts.order_by("-created_at")[:10]
        progression = []
        for a in reversed(list(recent_attempts)):
            total_qs = max(a.quiz.questions.count(), 1)
            progression.append({
                "date": a.created_at.strftime("%Y-%m-%d"),
                "quiz_title": a.quiz.title,
                "score_percentage": (a.score / total_qs) * 100
            })

        return Response({
            "total_documents": total_documents,
            "total_questions_asked": total_questions_asked,
            "total_quizzes_taken": total_quizzes_taken,
            "average_score": round(avg_score, 1),
            "weakest_concepts": top_weakest,
            "progression": progression
        })
