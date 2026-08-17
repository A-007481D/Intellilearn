import numpy as np
from apps.knowledge.models import DocumentChunk


class VectorRetriever:
    @staticmethod
    def retrieve_context(query_embedding, document_ids=None, top_k=5):
        """
        Retrieves the top_k most relevant chunks for a given query_embedding.
        Optionally filters by document_ids to restrict the search space.
        """
        qs = DocumentChunk.objects.all()

        if document_ids:
            qs = qs.filter(document_id__in=document_ids)

        chunks = list(qs)
        if not chunks:
            return []

        # Convert query embedding to numpy array
        q_vec = np.array(query_embedding)
        
        # Calculate L2 distance in memory since SQLite doesn't support pgvector operators
        scored_chunks = []
        for chunk in chunks:
            if chunk.embedding is None:
                continue
            c_vec = np.array(chunk.embedding)
            # L2 distance squared
            dist = np.sum((q_vec - c_vec) ** 2)
            scored_chunks.append((dist, chunk))
        
        # Sort by smallest distance (closest)
        scored_chunks.sort(key=lambda x: x[0])
        
        return [c[1] for c in scored_chunks[:top_k]]
