"""
LangGraph-based agentic framework for Enterprise Knowledge Operations.

This module implements a multi-agent system using LangGraph's state graphs
and node-based architecture for reliable, observable agent orchestration.
"""

from typing import Any, Dict, List, Optional, Annotated
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from core.types import Document, RetrievalResult, AnalysisResult, VerificationResult
from core.document_manager import DocumentManager
from config.settings import GROUNDING_THRESHOLD

logger = logging.getLogger(__name__)


class AgentNodeType(Enum):
    """Types of agent nodes in the graph."""
    ORCHESTRATOR = "orchestrator"
    RETRIEVER = "retriever"
    ANALYZER = "analyzer"
    VERIFIER = "verifier"
    MEMORY = "memory"
    ROUTER = "router"


@dataclass
class AgentState:
    """
    Shared state for all agents in the LangGraph.
    
    This state flows through the graph, updated by each agent node.
    Provides complete visibility into agent reasoning and decisions.
    """
    # Original query
    query: str = ""
    
    # Decomposed subtasks from Orchestrator
    subtasks: List[str] = field(default_factory=list)
    
    # Retrieved documents
    retrieved_documents: List[RetrievalResult] = field(default_factory=list)
    
    # Analysis results
    analysis_result: Optional[AnalysisResult] = None
    
    # Verification results
    verification_result: Optional[VerificationResult] = None
    
    # Conversation history
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution trace (for observability)
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    
    # Agent responses
    agent_responses: Dict[str, Any] = field(default_factory=dict)
    
    # Errors encountered
    errors: List[str] = field(default_factory=list)
    
    # Metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def add_trace(self, agent: str, step: str, details: Dict[str, Any] = None):
        """Add an entry to execution trace."""
        self.execution_trace.append({
            "agent": agent,
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
    
    def add_error(self, error: str):
        """Record an error."""
        self.errors.append(error)
        logger.error(f"Agent error: {error}")


class LangGraphAgentFramework:
    """
    Multi-agent framework using LangGraph for orchestration.
    
    Implements a state graph where:
    - Nodes are agent processing steps
    - Edges are transitions between agents
    - State flows through all agents
    - Each agent updates and passes state to next
    """
    
    def __init__(self, doc_manager: DocumentManager):
        """
        Initialize the LangGraph-based framework.
        
        Args:
            doc_manager: DocumentManager instance for document operations
        """
        self.doc_manager = doc_manager
        self.graph = self._build_graph()
        logger.info("LangGraph framework initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph.
        
        Graph structure:
        START → Router → Orchestrator → Retriever → Analyzer → Verifier → END
        
        Returns:
            Compiled StateGraph
        """
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agent processing steps)
        workflow.add_node("router", self._route_query)
        workflow.add_node("orchestrator", self._orchestrator_node)
        workflow.add_node("retriever", self._retriever_node)
        workflow.add_node("analyzer", self._analyzer_node)
        workflow.add_node("verifier", self._verifier_node)
        workflow.add_node("memory", self._memory_node)
        
        # Add edges (transitions)
        workflow.set_entry_point("router")
        
        # Router determines next step
        workflow.add_conditional_edges(
            "router",
            self._route_logic,
            {
                "orchestrator": "orchestrator",
                "memory": "memory",
                "end": END
            }
        )
        
        # Main pipeline: orchestrator → retriever → analyzer → verifier
        workflow.add_edge("orchestrator", "retriever")
        workflow.add_edge("retriever", "analyzer")
        workflow.add_edge("analyzer", "verifier")
        workflow.add_edge("verifier", "memory")
        workflow.add_edge("memory", END)
        
        # Compile the graph
        return workflow.compile()
    
    def _route_logic(self, state: AgentState) -> str:
        """
        Route query to appropriate agent.
        
        Logic:
        - If follow-up question: go to Memory
        - Otherwise: go to Orchestrator
        - If simple lookup: go to Retriever
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name
        """
        query = state.query.lower()
        
        # Detect follow-up questions
        if any(word in query for word in ["that", "it", "he", "she", "them"]):
            if state.conversation_history:
                return "memory"
        
        # Route to orchestrator for decomposition
        return "orchestrator"
    
    def _route_query(self, state: AgentState) -> AgentState:
        """
        Initial routing node.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state
        """
        state.started_at = datetime.now()
        state.add_trace("router", "query_received", {"query": state.query})
        return state
    
    def _orchestrator_node(self, state: AgentState) -> AgentState:
        """
        Orchestrator node: decompose query into subtasks.
        
        Uses template-based decomposition (can be replaced with LLM).
        
        Args:
            state: Agent state
            
        Returns:
            Updated state with subtasks
        """
        state.add_trace("orchestrator", "started", {})
        
        # Decompose query into subtasks
        query = state.query
        subtasks = self._decompose_query(query)
        state.subtasks = subtasks
        
        state.add_trace("orchestrator", "decomposed", {
            "num_subtasks": len(subtasks),
            "subtasks": subtasks
        })
        
        state.agent_responses["orchestrator"] = {
            "subtasks": subtasks,
            "count": len(subtasks)
        }
        
        return state
    
    def _retriever_node(self, state: AgentState) -> AgentState:
        """
        Retriever node: search for relevant documents.
        
        Performs semantic search on all subtasks.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state with retrieved documents
        """
        state.add_trace("retriever", "started", {})
        
        retrieved = []
        for subtask in state.subtasks:
            # Search for this subtask
            results = self.doc_manager.search(subtask, n_results=3)
            
            # Convert to RetrievalResult objects
            for result in results:
                retrieval_result = RetrievalResult(
                    chunk_id=result.get('id', ''),
                    content=result.get('content', ''),
                    document_id=result.get('id', '').split('_chunk_')[0],
                    source=result.get('metadata', {}).get('source', 'Unknown'),
                    relevance_score=1.0 - (result.get('distance', 0) / 2),
                    metadata=result.get('metadata', {})
                )
                retrieved.append(retrieval_result)
        
        state.retrieved_documents = retrieved
        
        state.add_trace("retriever", "completed", {
            "num_documents": len(retrieved),
            "avg_relevance": sum(d.relevance_score for d in retrieved) / len(retrieved) if retrieved else 0
        })
        
        state.agent_responses["retriever"] = {
            "documents_retrieved": len(retrieved),
            "avg_relevance": sum(d.relevance_score for d in retrieved) / len(retrieved) if retrieved else 0
        }
        
        return state
    
    def _analyzer_node(self, state: AgentState) -> AgentState:
        """
        Analyzer node: synthesize answer from documents.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state with analysis result
        """
        state.add_trace("analyzer", "started", {})
        
        if not state.retrieved_documents:
            answer = "No relevant documents found to answer this question."
        else:
            # Group by source
            by_source = {}
            for doc in state.retrieved_documents:
                if doc.source not in by_source:
                    by_source[doc.source] = []
                by_source[doc.source].append(doc)
            
            # Synthesize
            answer = f"Based on the retrieved documents, here's a comprehensive answer to your query:\n\n"
            answer += f"Query: {state.query}\n\n"
            answer += "Key Findings:\n\n"
            
            for i, (source, docs) in enumerate(by_source.items(), 1):
                answer += f"{i}. From {source}:\n"
                for doc in docs:
                    answer += f"   {doc.content}\n\n"
        
        # Create analysis result
        analysis_result = AnalysisResult(
            analysis_id=f"analysis_{len(state.execution_trace)}",
            query=state.query,
            subtasks=state.subtasks,
            retrieved_documents=state.retrieved_documents,
            synthesized_answer=answer,
            reasoning_steps=state.subtasks
        )
        state.analysis_result = analysis_result
        
        state.add_trace("analyzer", "completed", {
            "answer_length": len(answer),
            "num_sources": len(set(d.source for d in state.retrieved_documents))
        })
        
        state.agent_responses["analyzer"] = {
            "answer": answer[:200] + "..." if len(answer) > 200 else answer
        }
        
        return state
    
    def _verifier_node(self, state: AgentState) -> AgentState:
        """
        Verifier node: validate answer grounding.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state with verification results
        """
        state.add_trace("verifier", "started", {})
        
        if not state.analysis_result:
            state.add_error("No analysis result to verify")
            return state
        
        # Calculate grounding score
        avg_relevance = (
            sum(d.relevance_score for d in state.retrieved_documents) / len(state.retrieved_documents)
            if state.retrieved_documents else 0
        )
        
        if avg_relevance >= 0.5:
            grounding_score = min(0.8 + (avg_relevance * 0.2), 1.0)
        else:
            grounding_score = avg_relevance
        
        # Detect hallucinations
        hallucinations = []
        if len(state.analysis_result.synthesized_answer) > sum(
            len(d.content) for d in state.retrieved_documents
        ) * 3:
            hallucinations.append("Answer significantly longer than source material")
        
        # Determine confidence
        if grounding_score >= 0.8 and len(hallucinations) == 0:
            confidence = "high"
        elif grounding_score >= 0.6 and len(hallucinations) <= 1:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Create verification result
        verification_result = VerificationResult(
            verification_id=f"verification_{len(state.execution_trace)}",
            is_grounded=grounding_score >= GROUNDING_THRESHOLD,
            grounding_score=grounding_score,
            potential_hallucinations=hallucinations,
            confidence_level=confidence,
            validation_notes=f"Based on {len(state.retrieved_documents)} documents"
        )
        state.verification_result = verification_result
        
        state.add_trace("verifier", "completed", {
            "grounding_score": grounding_score,
            "confidence": confidence,
            "is_grounded": grounding_score >= GROUNDING_THRESHOLD
        })
        
        state.agent_responses["verifier"] = {
            "grounding_score": grounding_score,
            "confidence": confidence,
            "is_grounded": grounding_score >= GROUNDING_THRESHOLD
        }
        
        return state
    
    def _memory_node(self, state: AgentState) -> AgentState:
        """
        Memory node: update conversation history.
        
        Args:
            state: Agent state
            
        Returns:
            Updated state with memory
        """
        state.add_trace("memory", "started", {})
        
        # Add to conversation history
        state.conversation_history.append({
            "query": state.query,
            "answer": state.analysis_result.synthesized_answer if state.analysis_result else "",
            "grounding_score": state.verification_result.grounding_score if state.verification_result else 0,
            "confidence": state.verification_result.confidence_level if state.verification_result else "unknown",
            "timestamp": datetime.now().isoformat()
        })
        
        state.add_trace("memory", "updated", {
            "history_length": len(state.conversation_history)
        })
        
        state.completed_at = datetime.now()
        
        state.agent_responses["memory"] = {
            "history_stored": len(state.conversation_history)
        }
        
        return state
    
    def _decompose_query(self, query: str) -> List[str]:
        """
        Decompose query into subtasks.
        
        Template-based approach (can be replaced with LLM).
        
        Args:
            query: User query
            
        Returns:
            List of subtasks
        """
        # Template-based decomposition
        subtasks = [query]  # Start with main query
        
        # Add contextual subtasks
        if "what" in query.lower():
            subtasks.append(f"Context about {query}")
        if "how" in query.lower():
            subtasks.append(f"Process for {query}")
        if "why" in query.lower():
            subtasks.append(f"Reasons behind {query}")
        
        return subtasks
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a query through the LangGraph.
        
        Invokes the compiled state graph with the query.
        
        Args:
            query: User query
            
        Returns:
            Final state with all agent outputs
        """
        # Create initial state
        state = AgentState(query=query)
        
        logger.info(f"Processing query: {query}")
        
        # Invoke the graph
        try:
            final_state = self.graph.invoke(state)
            return self._format_response(final_state)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "error": str(e),
                "query": query,
                "execution_trace": state.execution_trace
            }
    
    def _format_response(self, state: AgentState) -> Dict[str, Any]:
        """
        Format final state into response.
        
        Args:
            state: Final agent state
            
        Returns:
            Formatted response dictionary
        """
        return {
            "query": state.query,
            "answer": state.analysis_result.synthesized_answer if state.analysis_result else "",
            "sources": [
                {
                    "source": doc.source,
                    "relevance": doc.relevance_score,
                    "content": doc.content[:100] + "..."
                }
                for doc in state.retrieved_documents
            ],
            "verification": {
                "grounded": state.verification_result.is_grounded if state.verification_result else False,
                "grounding_score": state.verification_result.grounding_score if state.verification_result else 0,
                "confidence": state.verification_result.confidence_level if state.verification_result else "unknown",
                "hallucinations": state.verification_result.potential_hallucinations if state.verification_result else []
            },
            "execution_trace": state.execution_trace,
            "agent_responses": state.agent_responses,
            "execution_time_ms": (
                (state.completed_at - state.started_at).total_seconds() * 1000
                if state.completed_at and state.started_at else 0
            ),
            "errors": state.errors
        }
