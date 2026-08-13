from apps.knowledge.models import DocumentChunk
from pgvector.django import L2Distance

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
            
        # Order by closest L2 distance (euclidean distance)
        chunks = qs.order_by(L2Distance('embedding', query_embedding))[:top_k]
        
        return list(chunks)
