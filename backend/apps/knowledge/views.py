import json

from django.http import StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document, DocumentStatus
from infrastructure.ai.gemini_adapter import GeminiEmbeddingService, GeminiLLMService
from infrastructure.ai.orchestrator import AgentOrchestrator
from infrastructure.ai.prompt_builder import QuizPromptBuilder
from infrastructure.ai.retriever import VectorRetriever

from .models import (
    Conversation,
    Message,
    Question,
    QuestionResponse,
    Quiz,
    QuizAttempt,
)
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
    """
    POST /api/v1/knowledge/chat/
    Regular JSON response (RAG-backed AI chat).

    Accepts:
      - question (str)
      - document_id (int, optional)
      - conversation_id (int, optional)
      - level (str: simple | standard | expert, default: standard)

    Returns:
      { conversation_id, answer, citations: [chunk_id, ...], intent, follow_up_actions }
    """

    permission_classes = [IsAuthenticated]

    def _generate_quiz_inline(self, request, contexts, document):
        prompt = QuizPromptBuilder.build_quiz_prompt(contexts, "medium", 5)
        llm_service = GeminiLLMService()
        try:
            answer = llm_service.generate_text(prompt)
            answer = answer.removeprefix("```json").removeprefix("```").removesuffix("```")
            questions_data = json.loads(answer.strip())

            quiz = Quiz.objects.create(
                user=request.user,
                document=document,
                title=f"{document.title} Quiz (Auto)",
                difficulty="medium",
            )
            for q_data in questions_data:
                chunk_ids = q_data.get("chunk_ids", [])
                q = Question.objects.create(
                    quiz=quiz,
                    question_type=Question.QuestionType.MCQ,
                    text=q_data.get("text", ""),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", ""),
                    concept=q_data.get("concept", ""),
                    explanation=q_data.get("explanation", ""),
                )
                if chunk_ids:
                    from apps.knowledge.models import DocumentChunk
                    q.source_chunks.set(
                        DocumentChunk.objects.filter(id__in=chunk_ids)
                    )
            return quiz
        except Exception:  # noqa: BLE001
            return None

    def post(self, request):
        question = request.data.get("question")
        document_id = request.data.get("document_id")
        conversation_id = request.data.get("conversation_id")
        level = request.data.get("level", "standard")

        if not question:
            return Response(
                {"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce READY status on selected document
        if document_id:
            try:
                doc_check = Document.objects.get(id=document_id, user=request.user)
                if doc_check.status != DocumentStatus.READY:
                    return Response(
                        {
                            "error": f"Document is not ready (status: {doc_check.status}). "
                            "Please wait for processing to complete."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Document.DoesNotExist:
                return Response(
                    {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Resolve or create conversation
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

        # Build history context (last 5 messages)
        history_qs = conversation.messages.order_by("-created_at")[:5]
        history = list(reversed(history_qs))

        # Generate query embedding
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

        quiz_id = None
        if intent == "QUIZ":
            doc = contexts[0].document if contexts else None
            if doc:
                quiz = self._generate_quiz_inline(request, contexts, doc)
                if quiz:
                    quiz_id = quiz.id
            answer = "I have generated a quiz based on your request. You can find it in the Quizzes tab."
        elif intent == "SUMMARY":
            try:
                llm = GeminiLLMService()
                ctx = "\n\n---\n\n".join([c.content for c in contexts])
                answer = llm.generate_text(
                    f"Summarize the following content concisely:\n\n{ctx}"
                )
            except Exception:  # noqa: BLE001
                answer = "Unable to generate summary at this time."
        else:
            try:
                answer = orchestrator.answer_question(question, history, level=level)
            except Exception:  # noqa: BLE001
                return Response(
                    {"error": "Failed to generate answer"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Build follow-up actions
        follow_up_actions = [
            {"label": "Deepen", "action": "deepen", "prompt": f"Go deeper on: {question}"},
            {"label": "Simplify", "action": "simplify", "prompt": f"Explain more simply: {question}"},
            {"label": "Quiz me", "action": "quiz", "prompt": f"Generate a quiz about: {question}"},
        ]

        # Persist messages
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
                "intent": intent,
                "citations": [
                    {
                        "id": c.id,
                        "page_number": c.page_number,
                        "content_preview": c.content[:120],
                        "document_id": c.document_id,
                    }
                    for c in contexts
                ],
                "follow_up_actions": follow_up_actions,
                **({"quiz_id": quiz_id} if quiz_id else {}),
            }
        )


class ChatStreamView(APIView):
    """
    GET /api/v1/knowledge/chat/stream/?question=...&document_id=...&conversation_id=...&level=...
    Server-Sent Events (SSE) streaming endpoint.
    Streams the AI response token by token.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        question = request.query_params.get("question")
        document_id = request.query_params.get("document_id")
        conversation_id = request.query_params.get("conversation_id")
        level = request.query_params.get("level", "standard")

        if not question:
            return Response(
                {"error": "question is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Enforce READY status
        if document_id:
            try:
                doc_check = Document.objects.get(id=document_id, user=request.user)
                if doc_check.status != DocumentStatus.READY:
                    return Response(
                        {"error": f"Document is not ready (status: {doc_check.status})."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Document.DoesNotExist:
                return Response(
                    {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Resolve conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id, user=request.user
                )
            except Conversation.DoesNotExist:
                return Response(
                    {"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            conversation = Conversation.objects.create(
                user=request.user, document_id=document_id, title=question[:50]
            )

        history_qs = conversation.messages.order_by("-created_at")[:5]
        history = list(reversed(history_qs))

        # Generate embedding
        try:
            embedding_service = GeminiEmbeddingService()
            query_embedding = embedding_service.generate_embeddings([question])[0]
        except Exception:  # noqa: BLE001
            return Response(
                {"error": "Failed to generate embedding"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        doc_ids = [int(document_id)] if document_id else None
        contexts = VectorRetriever.retrieve_context(
            query_embedding, document_ids=doc_ids, top_k=5
        )

        user = request.user

        def event_stream():
            """Generator that yields SSE-formatted chunks."""
            full_answer = []

            # Emit conversation_id first
            yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation.id, 'citations': [{'id': c.id, 'page_number': c.page_number, 'content_preview': c.content[:120], 'document_id': c.document_id} for c in contexts]})}\n\n"

            # Stream the answer using Gemini streaming
            try:
                from django.conf import settings
                from google import genai

                client = genai.Client(api_key=settings.GEMINI_API_KEY)

                from infrastructure.ai.prompt_builder import PromptBuilder

                prompt = PromptBuilder.build_rag_prompt(question, contexts, history)

                for chunk in client.models.generate_content_stream(
                    model="gemini-2.5-flash", contents=prompt
                ):
                    if chunk.text:
                        full_answer.append(chunk.text)
                        yield f"data: {json.dumps({'type': 'token', 'text': chunk.text})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

            # Save to DB
            final_answer = "".join(full_answer)
            Message.objects.create(
                conversation=conversation, role=Message.Role.USER, content=question
            )
            ai_msg = Message.objects.create(
                conversation=conversation, role=Message.Role.AI, content=final_answer
            )
            ai_msg.citations.set(contexts)

            yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation.id})}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class QuizGenerateView(APIView):
    """
    POST /api/v1/knowledge/quizzes/generate/
    Generates a quiz from a document.
    Supports question_type: mcq | true_false | open | mixed
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        document_id = request.data.get("document_id")
        difficulty = request.data.get("difficulty", "medium")
        num_questions = int(request.data.get("num_questions", 5))
        question_type = request.data.get("question_type", "mcq")  # mcq|true_false|open|mixed

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

        if document.status != DocumentStatus.READY:
            return Response(
                {"error": f"Document is not ready (status: {document.status})"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contexts = list(document.chunks.all()[:15])
        if not contexts:
            return Response(
                {"error": "Document has no processed chunks"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prompt = QuizPromptBuilder.build_quiz_prompt(
            contexts, difficulty, num_questions, question_type=question_type
        )

        llm_service = GeminiLLMService()
        try:
            answer = llm_service.generate_text(prompt)
            answer = answer.removeprefix("```json").removeprefix("```").removesuffix("```")
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
            q_type = q_data.get("question_type", Question.QuestionType.MCQ)
            if q_type not in Question.QuestionType.values:
                q_type = Question.QuestionType.MCQ

            q = Question.objects.create(
                quiz=quiz,
                question_type=q_type,
                text=q_data.get("text", ""),
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer", ""),
                concept=q_data.get("concept", ""),
                explanation=q_data.get("explanation", ""),
            )
            # Link to source chunks
            chunk_ids = q_data.get("chunk_ids", [])
            if chunk_ids:
                from apps.knowledge.models import DocumentChunk
                q.source_chunks.set(
                    DocumentChunk.objects.filter(id__in=chunk_ids, document=document)
                )

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizListView(generics.ListAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Quiz.objects.filter(user=self.request.user).order_by("-created_at")
        document_id = self.request.query_params.get("document_id")
        if document_id:
            qs = qs.filter(document_id=document_id)
        return qs


class QuizDetailView(generics.RetrieveAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)


class QuizSubmitView(APIView):
    """
    POST /api/v1/knowledge/quizzes/<pk>/submit/
    Submits quiz answers. For open questions, uses LLM semantic evaluation.
    """

    permission_classes = [IsAuthenticated]

    def _evaluate_open_answer(self, question_text, correct_answer, user_answer):
        """Semantically evaluates open-ended answers via LLM."""
        llm = GeminiLLMService()
        prompt = (
            f"You are an examiner. Evaluate this student answer.\n\n"
            f"Question: {question_text}\n"
            f"Expected answer: {correct_answer}\n"
            f"Student answer: {user_answer}\n\n"
            f"Return JSON only: {{\"is_correct\": true/false, \"score\": 0-100, \"feedback\": \"...\"}}"
        )
        try:
            result = llm.generate_text(prompt)
            result = result.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            data = json.loads(result)
            return data.get("is_correct", False), data.get("feedback", "")
        except Exception:  # noqa: BLE001
            # Fallback to exact match
            return user_answer.strip().lower() == correct_answer.strip().lower(), ""

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
        total = 0
        res_data = []

        for ans in answers:
            q_id = ans.get("question_id")
            user_ans = ans.get("answer", "")
            try:
                question = quiz.questions.get(id=q_id)
                total += 1

                if question.question_type == Question.QuestionType.OPEN:
                    is_correct, feedback = self._evaluate_open_answer(
                        question.text, question.correct_answer, user_ans
                    )
                else:
                    is_correct = question.correct_answer.strip().lower() == user_ans.strip().lower()
                    feedback = question.explanation

                if is_correct:
                    score += 1

                qr = QuestionResponse.objects.create(
                    attempt=attempt,
                    question=question,
                    user_answer=user_ans,
                    is_correct=is_correct,
                    feedback=feedback,
                )

                # Get source chunk info for citation link
                source_chunks = list(question.source_chunks.all()[:1])
                source = None
                if source_chunks:
                    c = source_chunks[0]
                    source = {
                        "chunk_id": c.id,
                        "page_number": c.page_number,
                        "document_id": c.document_id,
                    }

                res_data.append(
                    {
                        "question_id": question.id,
                        "question_type": question.question_type,
                        "user_answer": user_ans,
                        "is_correct": is_correct,
                        "correct_answer": question.correct_answer,
                        "explanation": question.explanation,
                        "feedback": feedback,
                        "source": source,
                    }
                )
            except Question.DoesNotExist:
                continue

        attempt.score = score
        attempt.save()

        return Response(
            {
                "attempt_id": attempt.id,
                "score": score,
                "total": total or quiz.questions.count(),
                "score_percentage": round((score / max(total, 1)) * 100, 1),
                "results": res_data,
            }
        )

class QuizAttemptDetailView(APIView):
    """
    GET /api/v1/knowledge/quizzes/attempts/<pk>/
    Fetches the full results of a previous quiz attempt.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            attempt = QuizAttempt.objects.select_related('quiz').get(pk=pk, user=request.user)
        except QuizAttempt.DoesNotExist:
            return Response({"error": "Attempt not found"}, status=status.HTTP_404_NOT_FOUND)

        res_data = []
        for qr in attempt.responses.select_related('question').all():
            question = qr.question
            source = None
            source_chunks = list(question.source_chunks.all()[:1])
            if source_chunks:
                c = source_chunks[0]
                source = {
                    "chunk_id": c.id,
                    "page_number": c.page_number,
                    "document_id": c.document_id,
                }

            res_data.append({
                "question_id": question.id,
                "question_type": question.question_type,
                "question_text": question.text,
                "user_answer": qr.user_answer,
                "is_correct": qr.is_correct,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "feedback": qr.feedback,
                "source": source,
            })

        total = attempt.quiz.questions.count()
        return Response({
            "quiz_id": attempt.quiz.id,
            "attempt_id": attempt.id,
            "score": attempt.score,
            "total": total,
            "score_percentage": round((attempt.score / max(total, 1)) * 100, 1),
            "results": res_data,
        })



class AnalyticsView(APIView):
    """
    GET /api/v1/knowledge/analytics/
    Query params:
      - document_id: filter by document
      - from_date: YYYY-MM-DD
      - to_date: YYYY-MM-DD
      - export: csv (optional)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        import csv
        from datetime import date, timedelta
        from io import StringIO

        user = request.user
        document_id = request.query_params.get("document_id")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        export_format = request.query_params.get("export")

        total_documents = Document.objects.filter(user=user).count()

        msg_qs = Message.objects.filter(
            conversation__user=user, role=Message.Role.USER
        )
        total_questions_asked = msg_qs.count()

        attempts_qs = QuizAttempt.objects.filter(user=user).prefetch_related(
            "quiz__questions"
        )
        if document_id:
            attempts_qs = attempts_qs.filter(quiz__document_id=document_id)
        if from_date:
            attempts_qs = attempts_qs.filter(created_at__date__gte=from_date)
        if to_date:
            attempts_qs = attempts_qs.filter(created_at__date__lte=to_date)

        attempts = list(attempts_qs.order_by("-created_at"))
        total_quizzes_taken = len(attempts)

        avg_score = 0.0
        if total_quizzes_taken > 0:
            avg_score = (
                sum(a.score / max(a.quiz.questions.count(), 1) * 100 for a in attempts)
                / total_quizzes_taken
            )

        # Concept tracking
        responses = QuestionResponse.objects.filter(
            attempt__user=user
        ).select_related("question")
        if document_id:
            responses = responses.filter(attempt__quiz__document_id=document_id)

        concept_stats: dict = {}
        for r in responses:
            concept = r.question.concept
            if not concept:
                continue
            if concept not in concept_stats:
                concept_stats[concept] = {"correct": 0, "total": 0}
            concept_stats[concept]["total"] += 1
            if r.is_correct:
                concept_stats[concept]["correct"] += 1

        weakest_concepts = []
        for concept, stats in concept_stats.items():
            rate = (stats["correct"] / stats["total"]) * 100
            weakest_concepts.append({"concept": concept, "success_rate": round(rate, 1)})
        weakest_concepts.sort(key=lambda x: x["success_rate"])
        top_weakest = weakest_concepts[:3]

        # Progression
        progression = []
        for a in reversed(attempts[:10]):
            total_qs = max(a.quiz.questions.count(), 1)
            progression.append(
                {
                    "id": a.id,
                    "date": a.created_at.strftime("%Y-%m-%d"),
                    "quiz_title": a.quiz.title,
                    "score_percentage": round((a.score / total_qs) * 100, 1),
                }
            )

        # Streak (assiduité) — consecutive days with at least 1 quiz attempt
        today = date.today()
        streak = 0
        check_date = today
        attempt_dates = set(
            QuizAttempt.objects.filter(user=user)
            .values_list("created_at__date", flat=True)
            .distinct()
        )
        while check_date in attempt_dates:
            streak += 1
            check_date -= timedelta(days=1)

        # Recommended actions
        recommended_actions = []
        for wc in top_weakest:
            recommended_actions.append(
                f"Review and practice more on: {wc['concept']} ({wc['success_rate']}% success rate)"
            )

        data = {
            "total_documents": total_documents,
            "total_questions_asked": total_questions_asked,
            "total_quizzes_taken": total_quizzes_taken,
            "average_score": round(avg_score, 1),
            "streak_days": streak,
            "weakest_concepts": top_weakest,
            "progression": progression,
            "recommended_actions": recommended_actions,
        }

        # CSV export
        if export_format == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Quiz Title", "Date", "Score (%)"])
            for p in progression:
                writer.writerow([p["quiz_title"], p["date"], p["score_percentage"]])
            from django.http import HttpResponse
            response = HttpResponse(output.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="analytics.csv"'
            return response

        return Response(data)


class DocumentSummaryView(APIView):
    """GET /api/v1/knowledge/documents/<pk>/summary/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if document.status != DocumentStatus.READY:
            return Response(
                {"error": "Document is not ready"}, status=status.HTTP_400_BAD_REQUEST
            )

        contexts = list(document.chunks.all()[:15])
        context_text = "\n\n---\n\n".join([c.content for c in contexts])

        prompt = f"""You are an expert educator. Based ONLY on the following document content, create:
1. A concise summary (3-5 sentences)
2. A structured fiche de synthèse (key concepts, main ideas, important terms)

Return valid JSON in this exact format:
{{
  "summary": "...",
  "fiche": {{
    "key_concepts": ["concept1", "concept2"],
    "main_ideas": ["idea1", "idea2"],
    "important_terms": {{"term": "definition"}}
  }}
}}

Document content:
{context_text}"""

        llm_service = GeminiLLMService()
        try:
            result = llm_service.generate_text(prompt)
            result = result.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return Response(
                {
                    "document_id": pk,
                    "title": document.title,
                    "data": json.loads(result),
                }
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": f"Failed to generate summary: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
