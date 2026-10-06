"""Analyzer agent for reasoning and synthesis using Google Gemini LLM."""

import logging
from typing import Any, Dict, List
import os

from agents.base_agent import BaseAgent
from config.settings import AgentRole
from core.types import AnalysisResult, RetrievalResult

logger = logging.getLogger(__name__)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("langchain_google_genai not available - will use template synthesis")


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
        Initialize analyzer agent with Google Gemini LLM.
        
        Args:
            llm: Language model for reasoning (uses Gemini if None)
            agent_id: Unique agent identifier
        """
        super().__init__(agent_id, AgentRole.ANALYZER)
        
        # Initialize Gemini LLM if not provided
        if llm is None and GEMINI_AVAILABLE:
            try:
                gemini_key = os.getenv('GOOGLE_API_KEY')
                if gemini_key:
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-pro",
                        google_api_key=gemini_key,
                        temperature=0.7,
                        max_output_tokens=2048
                    )
                    logger.info("Initialized Gemini LLM for analysis")
                else:
                    self.llm = None
                    logger.warning("GOOGLE_API_KEY not set - template synthesis will be used")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e} - using template synthesis")
                self.llm = None
        else:
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
        Synthesize an answer from retrieved documents using Gemini LLM.
        
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
        
        # Use Gemini LLM if available
        if self.llm is not None:
            try:
                from langchain.schema import HumanMessage
                
                prompt = f"""You are an expert knowledge assistant. Based on the following retrieved documents, 
provide a comprehensive, well-reasoned answer to the user's query.

USER QUERY: {query}

RETRIEVED DOCUMENTS:
{combined_content}

Instructions:
1. Provide a clear, comprehensive answer based on the documents
2. Cite specific sources when referencing information
3. Organize your response logically with key findings
4. Be concise but thorough
5. If information is not in the documents, say so clearly

ANSWER:"""
                
                response = self.llm.invoke([HumanMessage(content=prompt)])
                answer = response.content
                logger.info(f"Generated answer using Gemini LLM ({len(answer)} chars)")
                return answer
                
            except Exception as e:
                logger.warning(f"Gemini LLM invocation failed: {e} - falling back to template")
                return self._synthesize_answer_template(query, retrieval_results)
        else:
            # Fallback to template synthesis
            return self._synthesize_answer_template(query, retrieval_results)
    
    def _synthesize_answer_template(self, query: str, 
                                   retrieval_results: List[RetrievalResult]) -> str:
        """
        Fallback template-based answer synthesis (when LLM unavailable).
        
        Args:
            query: User query
            retrieval_results: Retrieved documents
            
        Returns:
            Synthesized answer
        """
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
