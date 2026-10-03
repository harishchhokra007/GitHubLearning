"""Core data structures and types for the AI system."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Document:
    """Represents an enterprise document."""
    id: str
    title: str
    content: str
    source_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    chunks: List["DocumentChunk"] = field(default_factory=list)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Represents a document retrieval result."""
    document_id: str
    chunk_id: str
    content: str
    relevance_score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    """Represents a message between agents."""
    agent_id: str
    agent_role: str
    message_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class QueryPlan:
    """Represents a decomposed query plan."""
    original_query: str
    plan_id: str
    subtasks: List["Subtask"] = field(default_factory=list)
    reasoning: str = ""
    execution_order: List[str] = field(default_factory=list)


@dataclass
class Subtask:
    """Represents a subtask in a query plan."""
    subtask_id: str
    agent_role: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1


@dataclass
class AnalysisResult:
    """Represents the result of analysis."""
    analysis_id: str
    query: str
    retrieved_documents: List[RetrievalResult]
    reasoning_steps: List[str]
    synthesized_answer: str
    source_references: List[Dict[str, Any]]


@dataclass
class VerificationResult:
    """Represents the result of verification."""
    verification_id: str
    is_grounded: bool
    grounding_score: float
    potential_hallucinations: List[str] = field(default_factory=list)
    confidence_level: str = "medium"  # low, medium, high
    validation_notes: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class EvaluationMetrics:
    """Represents evaluation metrics for a response."""
    query_id: str
    retrieval_relevance: float
    grounding_score: float
    hallucination_detected: bool
    execution_steps: List[str] = field(default_factory=list)
    agent_decisions: Dict[str, Any] = field(default_factory=dict)
    failure_flags: List[str] = field(default_factory=list)
    total_tokens_used: int = 0


@dataclass
class SystemResponse:
    """Final system response to a user query."""
    response_id: str
    query: str
    answer: str
    sources: List[RetrievalResult]
    agent_trace: List[AgentMessage]
    verification: VerificationResult
    evaluation: EvaluationMetrics
    execution_time_ms: float
    errors: List[str] = field(default_factory=list)
