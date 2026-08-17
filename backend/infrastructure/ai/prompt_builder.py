class PromptBuilder:
    @staticmethod
    def build_rag_prompt(question, contexts, history=None):
        """
        Builds a prompt that combines the user's question with the retrieved contexts.
        """
        context_text = "\n\n---\n\n".join([c.content for c in contexts])

        prompt = f"""You are a helpful AI assistant for an EdTech platform.
Please answer the user's question based strictly on the provided context below.
If the context does not contain the answer, say "I don't have enough information to answer that based on the documents."
Do not use outside knowledge.

Context:
{context_text}

        """
        if history:
            prompt += "\nChat History:\n"
            for msg in history:
                prompt += f"{msg.role.upper()}: {msg.content}\n"

        prompt += f"\nQuestion:\n{question}"
        return prompt


class QuizPromptBuilder:
    @staticmethod
    def build_quiz_prompt(contexts, difficulty="medium", num_questions=5):
        """
        Builds a prompt instructing the LLM to generate a quiz in a strict JSON format.
        """
        context_text = "\n\n---\n\n".join([c.content for c in contexts])

        prompt = f"""You are an expert educational assessment creator.
Based ONLY on the provided context, generate a {difficulty} difficulty multiple-choice quiz with exactly {num_questions} questions.

Your response MUST be a raw, valid JSON array of objects. Do not wrap the JSON in markdown code blocks. Do not add any conversational text.
Format requirements:
[
  {{
    "text": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "The exact string of the correct option",
    "concept": "The core concept being tested (1 to 3 words)",
    "explanation": "Why this answer is correct based on the text"
  }}
]

Context:
{context_text}
"""
        return prompt
