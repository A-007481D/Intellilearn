"""
Multi-agent orchestrator using CrewAI.
Implements 6 agents as per brief:
1. Orchestrator (Intent Classifier)
2. RAG Agent (passage retrieval context builder)
3. Pedagogical Agent (answer writer, adjusts to vulgarization level)
4. Generator Agent (quiz question creator)
5. Evaluator Agent (quiz correction, semantic evaluation)
6. Notification Agent (email dispatch coordinator)
"""
import json

try:
    from crewai import Agent, Crew, Process, Task
    from langchain_google_genai import ChatGoogleGenerativeAI
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Crew = Process = Task = ChatGoogleGenerativeAI = None

from django.conf import settings


class AgentOrchestrator:
    """Full 6-agent orchestrator as per the brief specification."""

    VULGARIZATION_LEVELS = {
        'simple': 'Use very simple language. Avoid technical jargon. Explain as if to a 10-year-old.',
        'standard': 'Use clear, accessible language for an educated adult learner.',
        'expert': 'Use precise technical vocabulary appropriate for a domain expert or researcher.',
    }

    def __init__(self, document_contexts=None):
        if CREWAI_AVAILABLE:
            self.llm = ChatGoogleGenerativeAI(
                model='gemini-1.5-flash', google_api_key=settings.GEMINI_API_KEY
            )
        else:
            self.llm = None
        self.context_chunks = document_contexts or []
        self.context_text = (
            '\n\n---\n\n'.join([c.content for c in self.context_chunks])
            if self.context_chunks
            else 'No context provided.'
        )

    def _make_agent(self, role, goal, backstory):
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
        )

    def _run_crew(self, agents, tasks):
        crew = Crew(agents=agents, tasks=tasks, process=Process.sequential)
        return str(crew.kickoff())

    # ------- Agent 1: Intent Classifier -------
    def classify_intent(self, user_prompt):
        """Classifies user intent as: QUIZ | SUMMARY | QNA"""
        if not CREWAI_AVAILABLE or not self.llm:
            return self._fallback_classify_intent(user_prompt)

        classifier = self._make_agent(
            role='Intent Classifier',
            goal='Classify the user intent as exactly one of: QUIZ, SUMMARY, or QNA.',
            backstory='You output a single word classification. QUIZ=user wants a quiz or test. SUMMARY=user wants a summary or fiche. QNA=any other question.',
        )
        task = Task(
            description=f'Classify this prompt. Output exactly one word (QUIZ, SUMMARY, or QNA): "{user_prompt}"',
            expected_output='A single word: QUIZ, SUMMARY, or QNA',
            agent=classifier,
        )
        result = self._run_crew([classifier], [task]).upper()
        if 'QUIZ' in result:
            return 'QUIZ'
        if 'SUMMARY' in result:
            return 'SUMMARY'
        return 'QNA'

    def _fallback_classify_intent(self, prompt):
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ['quiz', 'test', 'question', 'evaluate', 'examine']):
            return 'QUIZ'
        if any(w in prompt_lower for w in ['summary', 'summarize', 'fiche', 'resume', 'résumé']):
            return 'SUMMARY'
        return 'QNA'

    # ------- Agent 2+3: RAG + Pedagogical Agents -------
    def answer_question(self, user_prompt, history=None, level='standard'):
        """RAG agent retrieves context; Pedagogical agent writes the answer at the chosen level."""
        if not CREWAI_AVAILABLE or not self.llm:
            return self._fallback_answer(user_prompt)

        level_instruction = self.VULGARIZATION_LEVELS.get(level, self.VULGARIZATION_LEVELS['standard'])

        history_str = ''
        if history:
            history_str = 'Previous conversation:\n' + '\n'.join(
                [f'{msg.role.upper()}: {msg.content}' for msg in history]
            )

        # Agent 2: RAG retrieval (contextualizes what to use)
        rag_agent = self._make_agent(
            role='RAG Specialist',
            goal='Identify and extract the most relevant passages from the provided context to answer the question.',
            backstory='You are an expert at information retrieval. You find the exact passages needed to answer questions accurately.',
        )
        rag_task = Task(
            description=f'Given this document context, identify the most relevant passages to answer the question "{user_prompt}".\n\nContext:\n{self.context_text}',
            expected_output='The most relevant extracted passages from the context.',
            agent=rag_agent,
        )

        # Agent 3: Pedagogical response writer
        pedagogy_agent = self._make_agent(
            role='Expert Pedagogue',
            goal='Write a clear, accurate, educational answer tailored to the learner level.',
            backstory=f'You are a master teacher. Vulgarization level: {level_instruction}. You always cite the source passages you used. You never use external knowledge.',
        )
        pedagogy_task = Task(
            description=f'{history_str}\n\nUser question: {user_prompt}\n\nUsing the retrieved passages from the RAG agent, write a clear answer at the appropriate level with numbered citations.',
            expected_output='A well-structured educational answer with citations.',
            agent=pedagogy_agent,
            context=[rag_task],
        )

        return self._run_crew([rag_agent, pedagogy_agent], [rag_task, pedagogy_task])

    def _fallback_answer(self, prompt):
        from infrastructure.ai.gemini_adapter import GeminiLLMService
        from infrastructure.ai.prompt_builder import PromptBuilder
        llm = GeminiLLMService()
        p = PromptBuilder.build_rag_prompt(prompt, self.context_chunks)
        return llm.generate_text(p)

    # ------- Agent 4: Generator Agent -------
    def generate_quiz_questions(self, difficulty='medium', num_questions=5):
        """Generator agent creates quiz questions from the document context."""
        if not CREWAI_AVAILABLE or not self.llm:
            return None  # Fall back to direct LLM in view

        generator = self._make_agent(
            role='Quiz Generator',
            goal=f'Create exactly {num_questions} high-quality {difficulty} difficulty quiz questions from the provided content.',
            backstory='You are an expert assessment designer. You create clear, unambiguous MCQ questions with one correct answer and three plausible distractors. You always output valid JSON.',
        )
        task = Task(
            description=f'Generate {num_questions} {difficulty} difficulty multiple-choice questions from this content. Return a raw JSON array (no markdown):\n[{{"text": "...", "options": [...], "correct_answer": "...", "concept": "...", "explanation": "..."}}]\n\nContent:\n{self.context_text}',
            expected_output='A raw JSON array of quiz question objects.',
            agent=generator,
        )
        result = self._run_crew([generator], [task])
        try:
            return json.loads(result.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip())
        except Exception:
            return None

    # ------- Agent 5: Evaluator Agent -------
    def evaluate_open_answer(self, question_text, expected_answer, user_answer):
        """Evaluator agent semantically scores an open-ended answer."""
        if not CREWAI_AVAILABLE or not self.llm:
            return {'is_correct': False, 'score': 0, 'feedback': 'Evaluation unavailable.'}

        evaluator = self._make_agent(
            role='Assessment Evaluator',
            goal='Fairly evaluate a learner answer against the expected answer.',
            backstory='You are an expert examiner. You score answers from 0-100 based on conceptual accuracy, not just exact wording. You provide constructive feedback.',
        )
        task = Task(
            description=f'Question: {question_text}\nExpected answer: {expected_answer}\nLearner answer: {user_answer}\n\nEvaluate and return JSON: {{"score": 0-100, "is_correct": true/false, "feedback": "..."}}',
            expected_output='A JSON object with score, is_correct, and feedback fields.',
            agent=evaluator,
        )
        result = self._run_crew([evaluator], [task])
        try:
            return json.loads(result.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip())
        except Exception:
            return {'is_correct': False, 'score': 0, 'feedback': result}

    # ------- Agent 6: Notification Agent -------
    def generate_personalized_email(self, recipient_name, notification_type, context_data):
        """Notification agent generates a personalized email for a learner."""
        if not CREWAI_AVAILABLE or not self.llm:
            return self._fallback_email(recipient_name, notification_type, context_data)

        notification_agent = self._make_agent(
            role='Educational Notification Agent',
            goal='Write personalized, motivating email notifications for learners.',
            backstory='You are an EdTech communication specialist. You write warm, encouraging emails that motivate learners to continue their studies.',
        )
        task = Task(
            description=f'Write a personalized email for student "{recipient_name}" of type "{notification_type}". Context: {json.dumps(context_data)}. Include a call-to-action link placeholder [PLATFORM_LINK].',
            expected_output='A complete email with subject and body, ready to send.',
            agent=notification_agent,
        )
        return self._run_crew([notification_agent], [task])

    def _fallback_email(self, name, notification_type, context_data):
        return f'Hello {name},\n\nThis is a notification regarding: {notification_type}.\n\nBest regards,\nIntellilearn Team'
