"""Analyzer agent for reasoning and synthesis."""

import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from config.settings import AgentRole
from core.types import AnalysisResult, RetrievalResult

logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Analyzer agent responsible for:
    - Cross-document reasoning
    - Information synthesis
    - Answer generation
    - Logical inference
    """
    
    def __init__(self, llm=None, agent_id: str = "analyzer_1"):
        """
        Initialize analyzer agent.
        
        Args:
            llm: Language model for reasoning
            agent_id: Unique agent identifier
        """
        super().__init__(agent_id, AgentRole.ANALYZER)
        self.llm = llm
        
    def set_llm(self, llm):
        """Set the LLM to use for analysis."""
        self.llm = llm
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze retrieved documents and synthesize an answer.
        
        Args:
            input_data: Must contain 'query' and 'retrieval_results'
            
        Returns:
            Dictionary with analysis results
        """
        self.update_status("processing", "analyzing_documents")
        
        query = input_data.get('query', '')
        retrieval_results = input_data.get('retrieval_results', [])
        
        if not query:
            raise ValueError("Query is required for analysis")
        
        self.log_execution_step("Analysis started", {
            'query': query,
            'num_documents': len(retrieval_results)
        })
        
        # Extract reasoning steps
        reasoning_steps = await self._generate_reasoning_steps(query, retrieval_results)
        self.log_execution_step("Reasoning steps generated", {
            'num_steps': len(reasoning_steps)
        })
        
        # Synthesize answer
        synthesized_answer = await self._synthesize_answer(query, retrieval_results, reasoning_steps)
        self.log_execution_step("Answer synthesized", {
            'answer_length': len(synthesized_answer)
        })
        
        # Extract source references
        source_references = self._extract_source_references(retrieval_results)
        
        # Create analysis result
        analysis_result = AnalysisResult(
            analysis_id=f"analysis_{len(self.execution_trace)}",
            query=query,
            retrieved_documents=retrieval_results,
            reasoning_steps=reasoning_steps,
            synthesized_answer=synthesized_answer,
            source_references=source_references
        )
        
        self.state.results['analysis_result'] = analysis_result
        self.update_status("done")
        
        return {
            'analysis_result': analysis_result,
            'status': 'success'
        }
    
    async def _generate_reasoning_steps(self, query: str, 
                                       retrieval_results: List[RetrievalResult]) -> List[str]:
        """
        Generate reasoning steps for analysis.
        
        Args:
            query: User query
            retrieval_results: Retrieved documents
            
        Returns:
            List of reasoning steps
        """
        steps = []
        steps.append(f"Question: {query}")
        
        if retrieval_results:
            steps.append(f"Found {len(retrieval_results)} relevant documents")
            for i, result in enumerate(retrieval_results, 1):
                steps.append(f"  {i}. Source: {result.source} (relevance: {result.relevance_score:.2f})")
        
        steps.append("Synthesizing answer from multiple sources...")
        
        return steps
    
    async def _synthesize_answer(self, query: str, 
                                retrieval_results: List[RetrievalResult],
                                reasoning_steps: List[str]) -> str:
        """
        Synthesize an answer from retrieved documents.
        
        Args:
            query: User query
            retrieval_results: Retrieved documents
            reasoning_steps: Reasoning steps performed
            
        Returns:
            Synthesized answer
        """
        if not retrieval_results:
            return "I could not find any relevant documents to answer your question."
        
        # Combine retrieved content
        combined_content = "\n---\n".join([
            f"[{r.source}] {r.content}" 
            for r in retrieval_results
        ])
        
        # Generate answer (simplified - would use LLM in production)
        answer = f"""Based on the retrieved documents, here's a comprehensive answer to your query:

Query: {query}

Key Findings:
"""
        
        for i, result in enumerate(retrieval_results, 1):
            answer += f"\n{i}. From {result.metadata.get('title', result.source)}:\n"
            answer += f"   {result.content[:200]}...\n"
        
        answer += f"\n\nNote: This answer is synthesized from {len(retrieval_results)} source(s)."
        
        return answer
    
    @staticmethod
    def _extract_source_references(retrieval_results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """
        Extract source references from retrieval results.
        
        Args:
            retrieval_results: Retrieved documents
            
        Returns:
            List of source references
        """
        references = []
        seen_sources = set()
        
        for result in retrieval_results:
            source_key = result.source
            if source_key not in seen_sources:
                references.append({
                    'source': result.source,
                    'title': result.metadata.get('title', 'Unknown'),
                    'chunk_id': result.chunk_id,
                    'relevance_score': result.relevance_score
                })
                seen_sources.add(source_key)
        
        return references
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of analysis operations."""
        if 'analysis_result' not in self.state.results:
            return {}
        
        result = self.state.results['analysis_result']
        return {
            'analysis_id': result.analysis_id,
            'query': result.query,
            'num_documents': len(result.retrieved_documents),
            'num_reasoning_steps': len(result.reasoning_steps),
            'num_sources': len(result.source_references),
            'answer_length': len(result.synthesized_answer)
        }
