try:
    from crewai import Agent, Crew, Process, Task
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    Agent = Crew = Process = Task = ChatGoogleGenerativeAI = None

from django.conf import settings


class AgentOrchestrator:
    def __init__(self, document_contexts=None):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", google_api_key=settings.GEMINI_API_KEY
        )
        self.context_text = (
            "\n\n---\n\n".join([c.content for c in document_contexts])
            if document_contexts
            else "No context provided."
        )

    def classify_intent(self, user_prompt):
        classifier = Agent(
            role="Intent Classifier",
            goal="Classify the user intent strictly as QUIZ or QNA.",
            backstory="You only output a single word.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
        )
        task = Task(
            description=f'Classify the prompt as "QUIZ" if the user wants to generate a test/quiz, or "QNA" if asking a general question. Prompt: "{user_prompt}"',
            expected_output="A single word: QUIZ or QNA",
            agent=classifier,
        )
        crew = Crew(agents=[classifier], tasks=[task], process=Process.sequential)
        result = str(crew.kickoff())
        return "QUIZ" if "QUIZ" in result.upper() else "QNA"

    def answer_question(self, user_prompt, history=None):
        tutor = Agent(
            role="Expert Tutor",
            goal="Answer the user's question accurately based ONLY on the provided context.",
            backstory="You are a helpful educational tutor.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
        )
        history_str = ""
        if history:
            history_str = "Chat History:\n" + "\n".join(
                [f"{msg.role}: {msg.content}" for msg in history]
            )

        task = Task(
            description=f"Context: {self.context_text}\n\n{history_str}\n\nUser Question: {user_prompt}",
            expected_output="Detailed answer to the question.",
            agent=tutor,
        )
        crew = Crew(agents=[tutor], tasks=[task], process=Process.sequential)
        return str(crew.kickoff())
