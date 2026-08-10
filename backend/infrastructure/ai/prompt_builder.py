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
