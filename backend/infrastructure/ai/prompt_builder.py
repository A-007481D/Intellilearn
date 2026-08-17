class PromptBuilder:
    @staticmethod
    def build_rag_prompt(question, contexts, history=None):
        """
        Builds a RAG prompt combining the question with retrieved contexts.
        Produces numbered citations in the answer.
        """
        context_sections = []
        for i, c in enumerate(contexts, 1):
            context_sections.append(f"[{i}] (Page {c.page_number or '?'}): {c.content}")
        context_text = "\n\n".join(context_sections)

        prompt = f"""You are a helpful AI tutor for an EdTech platform.
You are having a conversation with a student.
If the student is just greeting you or making small talk, respond politely and naturally without referencing the documents.
Otherwise, answer the user's question based ONLY on the provided context below.
If the question is about the document and the context does not contain the answer, say "I don't have enough information based on the provided documents."
Do NOT use outside knowledge for facts. Include numbered citations like [1], [2] when referencing context passages.

Context:
{context_text}

"""
        if history:
            prompt += "\nPrevious conversation:\n"
            for msg in history:
                prompt += f"{msg.role.upper()}: {msg.content}\n"

        prompt += f"\nQuestion:\n{question}"
        return prompt


class QuizPromptBuilder:
    @staticmethod
    def build_quiz_prompt(
        contexts, difficulty="medium", num_questions=5, question_type="mcq"
    ):
        """
        Builds a quiz generation prompt.
        question_type: mcq | true_false | open | mixed
        """
        context_text = "\n\n---\n\n".join([c.content for c in contexts])
        chunk_ids = [c.id for c in contexts]

        if question_type == "mcq":
            format_desc = """[
  {{
    "question_type": "mcq",
    "text": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "The exact string of the correct option",
    "concept": "Core concept (1-3 words)",
    "explanation": "Why this answer is correct",
    "chunk_ids": [chunk_id_numbers_from_context]
  }}
]"""
        elif question_type == "true_false":
            format_desc = """[
  {{
    "question_type": "true_false",
    "text": "Statement to evaluate as true or false",
    "options": ["True", "False"],
    "correct_answer": "True or False",
    "concept": "Core concept (1-3 words)",
    "explanation": "Why this answer is correct",
    "chunk_ids": []
  }}
]"""
        elif question_type == "open":
            format_desc = """[
  {{
    "question_type": "open",
    "text": "The open-ended question",
    "options": [],
    "correct_answer": "Expected answer or key points",
    "concept": "Core concept (1-3 words)",
    "explanation": "Grading guidance",
    "chunk_ids": []
  }}
]"""
        else:  # mixed
            format_desc = """[
  {{
    "question_type": "mcq|true_false|open",
    "text": "Question text",
    "options": ["..."] or [],
    "correct_answer": "...",
    "concept": "Core concept",
    "explanation": "...",
    "chunk_ids": []
  }}
]"""

        prompt = f"""You are an expert educational assessment creator.
Based ONLY on the provided context, generate exactly {num_questions} {difficulty} difficulty questions of type "{question_type}".

Return a raw, valid JSON array (NO markdown, NO extra text):
{format_desc}

Available chunk IDs for citation: {chunk_ids}

Context:
{context_text}
"""
        return prompt
