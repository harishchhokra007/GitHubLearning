"""Configuration and constants for the AI Engineering Lead system."""

import os
from enum import Enum
from pathlib import Path

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
LOGS_DIR = PROJECT_ROOT / "logs"
EVAL_DIR = PROJECT_ROOT / "evaluation"

# Create directories if they don't exist
for dir_path in [DOCUMENTS_DIR, VECTOR_STORE_DIR, LOGS_DIR, EVAL_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Model Configuration
DEFAULT_LLM_MODEL = "gemini-pro"  # Google Gemini (free tier available)
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

# Gemini LLM Configuration
GEMINI_ENABLED = True  # Enable Gemini by default
GEMINI_MODEL = "gemini-pro"  # Model to use
GEMINI_TEMPERATURE = 0.7  # Creativity level (0.0-1.0)
GEMINI_MAX_TOKENS = 2048  # Maximum response length

# Vector Database Configuration
VECTOR_DB_TYPE = "chroma"  # Using Chroma for local, lightweight vector storage
VECTOR_DB_PERSIST_PATH = str(VECTOR_STORE_DIR)

# Chunking Configuration
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks

# Retrieval Configuration
TOP_K_RETRIEVAL = 5  # Number of top documents to retrieve
RETRIEVAL_SCORE_THRESHOLD = 0.6  # Minimum relevance score

# Grounding and Validation Configuration
GROUNDING_THRESHOLD = 0.7  # Confidence threshold for grounding validation
HALLUCINATION_THRESHOLD = 0.5  # Threshold for hallucination detection

# Agent Roles
class AgentRole(str, Enum):
    """Enumeration of agent roles in the system."""
    ORCHESTRATOR = "orchestrator"
    RETRIEVER = "retriever"
    ANALYZER = "analyzer"
    VERIFIER = "verifier"
    MEMORY = "memory"

# Message Types for Agent Communication
class MessageType(str, Enum):
    """Types of messages in the agent system."""
    QUERY = "query"
    RETRIEVAL_REQUEST = "retrieval_request"
    ANALYSIS_REQUEST = "analysis_request"
    VERIFICATION_REQUEST = "verification_request"
    RESPONSE = "response"
    ERROR = "error"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
