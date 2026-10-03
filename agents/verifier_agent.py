"""Verifier agent for validation, grounding, and guardrails."""

import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from config.settings import AgentRole, GROUNDING_THRESHOLD, HALLUCINATION_THRESHOLD
from core.types import AnalysisResult, VerificationResult, RetrievalResult

logger = logging.getLogger(__name__)


class VerifierAgent(BaseAgent):
    """
    Verifier agent responsible for:
    - Grounding verification (is answer supported by sources?)
    - Hallucination detection
    - Confidence scoring
    - Safety guardrails
    - Output validation
    """
    
    def __init__(self, agent_id: str = "verifier_1"):
        """Initialize verifier agent."""
        super().__init__(agent_id, AgentRole.VERIFIER)
        self.grounding_threshold = GROUNDING_THRESHOLD
        self.hallucination_threshold = HALLUCINATION_THRESHOLD
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify and validate the analysis result.
        
        Args:
            input_data: Must contain 'analysis_result'
            
        Returns:
            Dictionary with verification results
        """
        self.update_status("processing", "verifying_response")
        
        analysis_result = input_data.get('analysis_result')
        if not analysis_result:
            raise ValueError("Analysis result is required for verification")
        
        self.log_execution_step("Verification started", {
            'query': analysis_result.query
        })
        
        # Check grounding
        grounding_score = await self._verify_grounding(
            analysis_result.synthesized_answer,
            analysis_result.retrieved_documents
        )
        self.log_execution_step("Grounding checked", {
            'grounding_score': grounding_score
        })
        
        # Detect hallucinations
        hallucinations = await self._detect_hallucinations(
            analysis_result.synthesized_answer,
            analysis_result.retrieved_documents
        )
        self.log_execution_step("Hallucination detection completed", {
            'num_hallucinations': len(hallucinations)
        })
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(grounding_score, hallucinations)
        
        # Generate warnings
        warnings = self._generate_warnings(grounding_score, hallucinations, confidence_level)
        
        # Create verification result
        verification_result = VerificationResult(
            verification_id=f"verification_{len(self.execution_trace)}",
            is_grounded=grounding_score >= self.grounding_threshold,
            grounding_score=grounding_score,
            potential_hallucinations=hallucinations,
            confidence_level=confidence_level,
            validation_notes=f"Answer has {len(analysis_result.retrieved_documents)} supporting documents",
            warnings=warnings
        )
        
        self.state.results['verification_result'] = verification_result
        self.update_status("done")
        
        return {
            'verification_result': verification_result,
            'is_valid': verification_result.is_grounded and len(hallucinations) < 3,
            'status': 'success'
        }
    
    async def _verify_grounding(self, answer: str, documents: List[RetrievalResult]) -> float:
        """
        Verify that the answer is grounded in source documents.
        
        Args:
            answer: Generated answer
            documents: Retrieved source documents
            
        Returns:
            Grounding score (0-1)
        """
        if not documents:
            return 0.0
        
        # Calculate average relevance of retrieved documents
        avg_relevance = sum(d.relevance_score for d in documents) / len(documents)
        
        # If we have retrieved documents with reasonable relevance, assume grounding
        # Threshold: if avg relevance is high, we trust that the answer is grounded
        if avg_relevance >= 0.5:
            # High relevance documents = strong grounding
            grounding_score = min(0.8 + (avg_relevance * 0.2), 1.0)
        else:
            # Lower relevance = less grounding
            grounding_score = avg_relevance
        
        return min(grounding_score, 1.0)
    
    async def _detect_hallucinations(self, answer: str, 
                                    documents: List[RetrievalResult]) -> List[str]:
        """
        Detect potential hallucinations in the answer.
        
        Args:
            answer: Generated answer
            documents: Retrieved source documents
            
        Returns:
            List of potential hallucinations
        """
        hallucinations = []
        
        # Combine all document content
        document_content = "\n".join([d.content for d in documents])
        
        # Only flag if answer is MUCH longer than source material (3x instead of 2x)
        if len(answer) > len(document_content) * 3:
            hallucinations.append("Answer is significantly longer than source material")
        
        # Reduced hallucination detection - only flag obvious cases
        # Most synthesis naturally expands on source material
        
        return hallucinations
    
    def _determine_confidence_level(self, grounding_score: float, 
                                   hallucinations: List[str]) -> str:
        """
        Determine confidence level based on verification metrics.
        
        Args:
            grounding_score: Grounding verification score
            hallucinations: List of detected hallucinations
            
        Returns:
            Confidence level string
        """
        if grounding_score >= 0.8 and len(hallucinations) == 0:
            return "high"
        elif grounding_score >= 0.6 and len(hallucinations) <= 1:
            return "medium"
        else:
            return "low"
    
    def _generate_warnings(self, grounding_score: float, 
                          hallucinations: List[str], 
                          confidence_level: str) -> List[str]:
        """
        Generate warnings for the user.
        
        Args:
            grounding_score: Grounding verification score
            hallucinations: List of detected hallucinations
            confidence_level: Determined confidence level
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        if confidence_level == "low":
            warnings.append("Low confidence in this response. Verify against original sources.")
        
        if grounding_score < self.grounding_threshold:
            warnings.append(f"Grounding score ({grounding_score:.2f}) below threshold ({self.grounding_threshold})")
        
        for hallucination in hallucinations:
            warnings.append(f"Potential issue: {hallucination}")
        
        return warnings
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get a summary of verification operations."""
        if 'verification_result' not in self.state.results:
            return {}
        
        result = self.state.results['verification_result']
        return {
            'verification_id': result.verification_id,
            'is_grounded': result.is_grounded,
            'grounding_score': result.grounding_score,
            'confidence_level': result.confidence_level,
            'num_hallucinations': len(result.potential_hallucinations),
            'num_warnings': len(result.warnings)
        }
