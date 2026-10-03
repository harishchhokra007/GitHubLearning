"""Retriever agent for document search and retrieval."""

import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from config.settings import AgentRole, TOP_K_RETRIEVAL, RETRIEVAL_SCORE_THRESHOLD
from core.document_manager import DocumentManager
from core.types import RetrievalResult

logger = logging.getLogger(__name__)


class RetrieverAgent(BaseAgent):
    """
    Retriever agent responsible for:
    - Semantic search over documents
    - Ranking and filtering results
    - Preserving source attribution
    - Relevance scoring
    """
    
    def __init__(self, document_manager: DocumentManager, agent_id: str = "retriever_1"):
        """
        Initialize retriever agent.
        
        Args:
            document_manager: DocumentManager instance for vector search
            agent_id: Unique agent identifier
        """
        super().__init__(agent_id, AgentRole.RETRIEVER)
        self.document_manager = document_manager
        self.top_k = TOP_K_RETRIEVAL
        self.score_threshold = RETRIEVAL_SCORE_THRESHOLD
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            input_data: Must contain 'query' key
            
        Returns:
            Dictionary with retrieval results
        """
        self.update_status("processing", "searching_documents")
        
        query = input_data.get('query', '')
        if not query:
            raise ValueError("Query is required for retrieval")
        
        top_k = input_data.get('top_k', self.top_k)
        threshold = input_data.get('score_threshold', self.score_threshold)
        
        self.log_execution_step("Retrieval started", {'query': query})
        
        # Perform semantic search
        search_results = self.document_manager.search(query, top_k=top_k)
        self.log_execution_step("Semantic search completed", {'num_results': len(search_results)})
        
        # Filter and rank results
        retrieval_results = []
        for result in search_results:
            relevance_score = result.get('relevance_score', 0)
            
            # Apply threshold filtering
            if relevance_score >= threshold:
                retrieval_result = RetrievalResult(
                    document_id=result.get('metadata', {}).get('source', 'unknown'),
                    chunk_id=result.get('id', ''),
                    content=result.get('content', ''),
                    relevance_score=relevance_score,
                    source=result.get('metadata', {}).get('source', 'unknown'),
                    metadata=result.get('metadata', {})
                )
                retrieval_results.append(retrieval_result)
        
        self.log_execution_step("Results filtered", {
            'total_results': len(search_results),
            'filtered_results': len(retrieval_results),
            'threshold': threshold
        })
        
        self.state.results['retrieval_results'] = retrieval_results
        self.update_status("done")
        
        return {
            'retrieval_results': retrieval_results,
            'query': query,
            'num_results': len(retrieval_results),
            'status': 'success'
        }
    
    def get_retrieval_summary(self) -> Dict[str, Any]:
        """Get a summary of retrieval operations."""
        if 'retrieval_results' not in self.state.results:
            return {}
        
        results = self.state.results['retrieval_results']
        return {
            'num_retrieved': len(results),
            'avg_relevance': sum(r.relevance_score for r in results) / len(results) if results else 0,
            'results': [
                {
                    'chunk_id': r.chunk_id,
                    'relevance_score': r.relevance_score,
                    'source': r.source
                }
                for r in results
            ]
        }
