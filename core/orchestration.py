"""Main orchestration system using LangGraph for workflow management."""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from agents.base_agent import AgentRegistry, BaseAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.retriever_agent import RetrieverAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.verifier_agent import VerifierAgent
from agents.memory_agent import MemoryAgent
from core.document_manager import DocumentManager
from core.types import SystemResponse, AgentMessage
from evaluation.evaluation_system import EvaluationSystem
from config.settings import AgentRole

logger = logging.getLogger(__name__)


class EnterpriseKnowledgeAgent:
    """
    Main orchestration system for the Enterprise Knowledge Operations Agent.
    Coordinates all specialized agents and manages the complete workflow.
    """
    
    def __init__(self, document_manager: Optional[DocumentManager] = None):
        """
        Initialize the enterprise knowledge agent.
        
        Args:
            document_manager: DocumentManager instance for document operations
        """
        self.agent_registry = AgentRegistry()
        self.document_manager = document_manager or DocumentManager()
        self.evaluation_system = EvaluationSystem()
        
        # Initialize agents
        self._initialize_agents()
        
        # State management
        self.conversation_state: Dict[str, Any] = {}
        self.execution_traces: List[Dict[str, Any]] = []
        
    def _initialize_agents(self) -> None:
        """Initialize all specialized agents."""
        logger.info("Initializing agent system...")
        
        # Create orchestrator
        orchestrator = OrchestratorAgent()
        self.agent_registry.register(orchestrator)
        
        # Create retriever
        retriever = RetrieverAgent(self.document_manager)
        self.agent_registry.register(retriever)
        
        # Create analyzer
        analyzer = AnalyzerAgent()
        self.agent_registry.register(analyzer)
        
        # Create verifier
        verifier = VerifierAgent()
        self.agent_registry.register(verifier)
        
        # Create memory
        memory = MemoryAgent()
        self.agent_registry.register(memory)
        
        logger.info(f"Initialized {len(self.agent_registry.list_agents())} agents")
    
    async def process_query(self, query: str, top_k: int = 5) -> SystemResponse:
        """
        Process a user query through the multi-agent system.
        
        Args:
            query: User query to process
            top_k: Number of top documents to retrieve
            
        Returns:
            SystemResponse with answer and evaluation
        """
        start_time = time.time()
        response_id = str(uuid.uuid4())[:8]
        agent_trace: List[AgentMessage] = []
        errors: List[str] = []
        
        logger.info(f"Processing query: {query} (Response ID: {response_id})")
        
        try:
            # Step 1: Orchestrator - Plan the query
            logger.info("STEP 1: Orchestrator planning...")
            orchestrator = self.agent_registry.get_agent("orchestrator_1")
            plan_result = await orchestrator.process({'query': query})
            self._log_agent_activity(orchestrator, agent_trace)
            
            # Step 2: Retriever - Get relevant documents
            logger.info("STEP 2: Retriever searching documents...")
            retriever = self.agent_registry.get_agent("retriever_1")
            retrieval_result = await retriever.process({
                'query': query,
                'top_k': top_k
            })
            self._log_agent_activity(retriever, agent_trace)
            retrieval_results = retrieval_result.get('retrieval_results', [])
            
            # Step 3: Analyzer - Synthesize answer
            logger.info("STEP 3: Analyzer synthesizing answer...")
            analyzer = self.agent_registry.get_agent("analyzer_1")
            analysis_result = await analyzer.process({
                'query': query,
                'retrieval_results': retrieval_results
            })
            self._log_agent_activity(analyzer, agent_trace)
            analysis = analysis_result.get('analysis_result')
            
            # Step 4: Verifier - Validate response
            logger.info("STEP 4: Verifier validating response...")
            verifier = self.agent_registry.get_agent("verifier_1")
            verification_result = await verifier.process({
                'analysis_result': analysis
            })
            self._log_agent_activity(verifier, agent_trace)
            verification = verification_result.get('verification_result')
            
            # Step 5: Memory - Store in context
            logger.info("STEP 5: Memory storing results...")
            memory = self.agent_registry.get_agent("memory_1")
            # Store response info (simplified)
            
            # Create final system response
            execution_time_ms = (time.time() - start_time) * 1000
            
            final_response = SystemResponse(
                response_id=response_id,
                query=query,
                answer=analysis.synthesized_answer,
                sources=retrieval_results,
                agent_trace=agent_trace,
                verification=verification,
                evaluation=None,  # Will be set below
                execution_time_ms=execution_time_ms,
                errors=errors
            )
            
            # Evaluate response
            logger.info("Evaluating response...")
            metrics = self.evaluation_system.evaluate_response(final_response, agent_trace)
            final_response.evaluation = metrics
            
            # Log evaluation report
            self.evaluation_system.log_evaluation_report(final_response, metrics)
            
            # Save evaluation
            self.evaluation_system.save_evaluation(final_response, metrics)
            
            logger.info(f"Query processing complete. Time: {execution_time_ms:.2f}ms")
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            errors.append(str(e))
            
            # Return error response
            from core.types import VerificationResult, EvaluationMetrics
            
            error_response = SystemResponse(
                response_id=response_id,
                query=query,
                answer=f"Error processing query: {str(e)}",
                sources=[],
                agent_trace=agent_trace,
                verification=VerificationResult(
                    verification_id=f"ver_{response_id}",
                    is_grounded=False,
                    grounding_score=0.0,
                    confidence_level="low",
                    warnings=["Error during processing"]
                ),
                evaluation=EvaluationMetrics(
                    query_id=response_id,
                    retrieval_relevance=0.0,
                    grounding_score=0.0,
                    hallucination_detected=False,
                    failure_flags=["Processing error"]
                ),
                execution_time_ms=(time.time() - start_time) * 1000,
                errors=errors
            )
            
            return error_response
    
    def _log_agent_activity(self, agent: BaseAgent, agent_trace: List[AgentMessage]) -> None:
        """
        Log agent activity to trace.
        
        Args:
            agent: Agent that executed
            agent_trace: List to append to
        """
        for step in agent.execution_trace:
            trace_msg = AgentMessage(
                agent_id=agent.agent_id,
                agent_role=agent.role.value,
                message_type="execution_trace",
                content=f"{step.get('step_name', 'unknown')}: {str(step.get('details', ''))}",
                metadata=step.get('details', {})
            )
            agent_trace.append(trace_msg)
    
    def ingest_document(self, file_path: str) -> None:
        """
        Ingest a document into the system.
        
        Args:
            file_path: Path to document file
        """
        logger.info(f"Ingesting document: {file_path}")
        self.document_manager.ingest_document(file_path)
    
    def ingest_text(self, text: str, title: str) -> None:
        """
        Ingest text into the system.
        
        Args:
            text: Text content
            title: Document title
        """
        logger.info(f"Ingesting text document: {title}")
        self.document_manager.ingest_text(text, title)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and metrics.
        
        Returns:
            Dictionary with system status
        """
        agents = self.agent_registry.list_agents()
        eval_summary = self.evaluation_system.get_evaluation_summary()
        
        return {
            'agents_registered': len(agents),
            'agents': agents,
            'documents_loaded': len(self.document_manager.documents),
            'evaluations_performed': eval_summary.get('total_evaluations', 0),
            'evaluation_summary': eval_summary
        }
    
    def format_response(self, response: SystemResponse) -> str:
        """
        Format response for user display.
        
        Args:
            response: SystemResponse to format
            
        Returns:
            Formatted response string
        """
        formatted = f"""
{'='*70}
QUERY: {response.query}
{'='*70}

ANSWER:
{response.answer}

{'='*70}
SOURCES:
"""
        for i, source in enumerate(response.sources, 1):
            formatted += f"\n{i}. {source.source} (Relevance: {source.relevance_score:.2f})"
        
        formatted += f"""

{'='*70}
VERIFICATION:
- Grounded: {response.verification.is_grounded}
- Grounding Score: {response.verification.grounding_score:.2f}
- Confidence: {response.verification.confidence_level}
- Hallucinations Detected: {len(response.verification.potential_hallucinations) > 0}

{'='*70}
EVALUATION:
- Retrieval Relevance: {response.evaluation.retrieval_relevance:.2f}
- Failure Flags: {len(response.evaluation.failure_flags)}

Execution Time: {response.execution_time_ms:.2f}ms
{'='*70}
"""
        
        if response.verification.warnings:
            formatted += "\nWARNINGS:\n"
            for warning in response.verification.warnings:
                formatted += f"  ⚠ {warning}\n"
        
        return formatted
