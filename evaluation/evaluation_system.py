"""Evaluation system for monitoring, assessment, and observability."""

import logging
import json
from typing import Any, Dict, List
from datetime import datetime
from pathlib import Path

from config.settings import EVAL_DIR, LOGS_DIR
from core.types import SystemResponse, EvaluationMetrics, VerificationResult, RetrievalResult

logger = logging.getLogger(__name__)


class EvaluationSystem:
    """
    Evaluation system responsible for:
    - Grounding checks
    - Retrieval relevance scoring
    - Agent decision tracing
    - Failure detection
    - Structured logging
    """
    
    def __init__(self):
        """Initialize evaluation system."""
        self.eval_results: List[Dict[str, Any]] = []
        self.eval_dir = Path(EVAL_DIR)
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        
    def evaluate_response(self, response: SystemResponse, 
                         traces: List[Dict[str, Any]] = None) -> EvaluationMetrics:
        """
        Comprehensive evaluation of a system response.
        
        Args:
            response: SystemResponse to evaluate
            traces: Agent decision traces
            
        Returns:
            EvaluationMetrics object
        """
        logger.info(f"Starting evaluation for response: {response.response_id}")
        
        # Evaluate retrieval relevance
        retrieval_relevance = self._evaluate_retrieval_relevance(response.sources)
        logger.info(f"Retrieval relevance: {retrieval_relevance:.2f}")
        
        # Get grounding score from verification
        grounding_score = response.verification.grounding_score
        logger.info(f"Grounding score: {grounding_score:.2f}")
        
        # Detect hallucinations
        hallucination_detected = len(response.verification.potential_hallucinations) > 0
        logger.info(f"Hallucination detected: {hallucination_detected}")
        
        # Extract execution steps
        execution_steps = self._extract_execution_steps(response.agent_trace)
        
        # Extract agent decisions
        agent_decisions = self._extract_agent_decisions(response.agent_trace)
        
        # Detect failures
        failure_flags = self._detect_failures(response, retrieval_relevance, grounding_score)
        
        # Create evaluation metrics
        metrics = EvaluationMetrics(
            query_id=response.response_id,
            retrieval_relevance=retrieval_relevance,
            grounding_score=grounding_score,
            hallucination_detected=hallucination_detected,
            execution_steps=execution_steps,
            agent_decisions=agent_decisions,
            failure_flags=failure_flags,
            total_tokens_used=0  # Would track actual token usage
        )
        
        # Log evaluation
        self.eval_results.append({
            'response_id': response.response_id,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Evaluation complete. Failure flags: {len(failure_flags)}")
        return metrics
    
    def _evaluate_retrieval_relevance(self, sources: List[RetrievalResult]) -> float:
        """
        Evaluate the relevance of retrieved documents.
        
        Args:
            sources: Retrieved source documents
            
        Returns:
            Average relevance score
        """
        if not sources:
            return 0.0
        
        relevance_scores = [s.relevance_score for s in sources]
        avg_relevance = sum(relevance_scores) / len(relevance_scores)
        
        return avg_relevance
    
    @staticmethod
    def _extract_execution_steps(agent_trace: List[Dict[str, Any]]) -> List[str]:
        """
        Extract execution steps from agent trace.
        
        Args:
            agent_trace: Agent execution trace
            
        Returns:
            List of execution step descriptions
        """
        steps = []
        for msg in agent_trace:
            if isinstance(msg, dict):
                steps.append(f"{msg.get('agent_id', 'unknown')}: {msg.get('content', '')}")
            else:
                steps.append(str(msg))
        return steps
    
    @staticmethod
    def _extract_agent_decisions(agent_trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract key agent decisions from trace.
        
        Args:
            agent_trace: Agent execution trace
            
        Returns:
            Dictionary of agent decisions
        """
        decisions = {}
        for msg in agent_trace:
            if isinstance(msg, dict):
                agent_id = msg.get('agent_id', 'unknown')
                if agent_id not in decisions:
                    decisions[agent_id] = []
                decisions[agent_id].append({
                    'message_type': msg.get('message_type', 'unknown'),
                    'content_preview': msg.get('content', '')[:100]
                })
        return decisions
    
    @staticmethod
    def _detect_failures(response: SystemResponse, 
                        retrieval_relevance: float,
                        grounding_score: float) -> List[str]:
        """
        Detect system failures and issues.
        
        Args:
            response: System response
            retrieval_relevance: Retrieval relevance score
            grounding_score: Grounding score
            
        Returns:
            List of detected failure flags
        """
        failures = []
        
        # Check for insufficient retrieval
        if len(response.sources) == 0:
            failures.append("No documents retrieved")
        elif retrieval_relevance < 0.5:
            failures.append(f"Low retrieval relevance: {retrieval_relevance:.2f}")
        
        # Check for low grounding confidence
        if grounding_score < 0.6:
            failures.append(f"Low grounding score: {grounding_score:.2f}")
        
        # Check for hallucinations
        if response.verification.potential_hallucinations:
            failures.append(f"Potential hallucinations detected: {len(response.verification.potential_hallucinations)}")
        
        # Check for system errors
        if response.errors:
            failures.append(f"System errors: {len(response.errors)}")
        
        return failures
    
    def save_evaluation(self, response: SystemResponse, metrics: EvaluationMetrics) -> str:
        """
        Save evaluation results to file.
        
        Args:
            response: System response
            metrics: Evaluation metrics
            
        Returns:
            Path to saved evaluation file
        """
        eval_data = {
            'response_id': response.response_id,
            'query': response.query,
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'retrieval_relevance': metrics.retrieval_relevance,
                'grounding_score': metrics.grounding_score,
                'hallucination_detected': metrics.hallucination_detected,
                'failure_flags': metrics.failure_flags,
                'num_execution_steps': len(metrics.execution_steps),
                'num_agent_decisions': len(metrics.agent_decisions)
            },
            'verification': {
                'is_grounded': response.verification.is_grounded,
                'confidence_level': response.verification.confidence_level,
                'warnings': response.verification.warnings
            }
        }
        
        # Save to JSON file
        filename = self.eval_dir / f"eval_{response.response_id}.json"
        with open(filename, 'w') as f:
            json.dump(eval_data, f, indent=2)
        
        logger.info(f"Evaluation saved to {filename}")
        return str(filename)
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all evaluations.
        
        Returns:
            Dictionary with evaluation summary statistics
        """
        if not self.eval_results:
            return {}
        
        avg_retrieval = sum(r['metrics'].retrieval_relevance for r in self.eval_results) / len(self.eval_results)
        avg_grounding = sum(r['metrics'].grounding_score for r in self.eval_results) / len(self.eval_results)
        hallucination_count = sum(1 for r in self.eval_results if r['metrics'].hallucination_detected)
        failure_count = sum(len(r['metrics'].failure_flags) for r in self.eval_results)
        
        return {
            'total_evaluations': len(self.eval_results),
            'avg_retrieval_relevance': avg_retrieval,
            'avg_grounding_score': avg_grounding,
            'responses_with_hallucinations': hallucination_count,
            'total_failure_flags': failure_count,
            'success_rate': (len(self.eval_results) - hallucination_count) / len(self.eval_results) * 100
        }
    
    def log_evaluation_report(self, response: SystemResponse, metrics: EvaluationMetrics) -> None:
        """
        Log comprehensive evaluation report.
        
        Args:
            response: System response
            metrics: Evaluation metrics
        """
        report = f"""
================== EVALUATION REPORT ==================
Response ID: {response.response_id}
Query: {response.query}
Timestamp: {datetime.now().isoformat()}

--- RETRIEVAL EVALUATION ---
Relevance Score: {metrics.retrieval_relevance:.2f}
Documents Retrieved: {len(response.sources)}

--- GROUNDING EVALUATION ---
Grounding Score: {metrics.grounding_score:.2f}
Is Grounded: {response.verification.is_grounded}
Confidence Level: {response.verification.confidence_level}

--- HALLUCINATION DETECTION ---
Hallucinations Detected: {metrics.hallucination_detected}
Count: {len(response.verification.potential_hallucinations)}

--- FAILURE DETECTION ---
Failure Flags: {len(metrics.failure_flags)}
{chr(10).join([f"  - {flag}" for flag in metrics.failure_flags])}

--- WARNINGS ---
{chr(10).join([f"  - {warning}" for warning in response.verification.warnings])}

--- EXECUTION TRACE ---
Steps: {len(metrics.execution_steps)}
{chr(10).join([f"  {i+1}. {step}" for i, step in enumerate(metrics.execution_steps[:5])])}
{'...' if len(metrics.execution_steps) > 5 else ''}

========================================================
"""
        logger.info(report)
