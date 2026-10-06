# Enterprise Knowledge Operations Agent - Architecture Documentation

## Overview

The Enterprise Knowledge Operations Agent is a production-grade multi-agent AI system built with **LangGraph**, designed to answer complex enterprise questions by reasoning across multiple documents. It implements state graph-based agent orchestration for reliability and observability.

## System Architecture - LangGraph Framework

### LangGraph State Graph

```
                   ┌─────────────────────────┐
                   │   AgentState (Shared)    │
                   │ - Query                  │
                   │ - Subtasks               │
                   │ - Retrieved Documents    │
                   │ - Analysis Result        │
                   │ - Verification Result    │
                   │ - Execution Trace        │
                   │ - Conversation History   │
                   └─────────────────────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
          ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
          │  Router  │→  │Orchestrator├→ │Retriever│
          │  Node    │   │   Node    │  │  Node   │
          └─────────┘   └────┬──────┘  └────┬────┘
                              │              │
                       ┌──────▼──────┐      │
                       │  Analyzer   │◄─────┘
                       │   Node      │
                       └──────┬──────┘
                              │
                       ┌──────▼──────┐
                       │  Verifier   │
                       │   Node      │
                       └──────┬──────┘
                              │
                       ┌──────▼──────┐
                       │   Memory    │
                       │   Node      │
                       └──────┬──────┘
                              │
                           [END]
```

### LangGraph Advantages

1. **State Management**: All agents access shared AgentState
2. **Observability**: Execution trace at each node
3. **Error Handling**: Graceful error propagation through state
4. **Scalability**: Easy to add new nodes/agents
5. **Testability**: State changes are trackable
6. **Debugging**: Full execution history available

## Component Description

### Architecture Layers

```
┌──────────────────────────────────────────────────┐
│  User Interface / Query Entry Point              │
│  (main.py interactive loop)                      │
└──────────────────┬───────────────────────────────┘
                  │
┌──────────────────▼───────────────────────────────┐
│  LangGraph State Graph (langgraph_framework.py)   │
│  ┌──────────────────────────────────────────┐   │
│  │ Router Node                              │   │
│  │ ├─ Classify query type                  │   │
│  │ └─ Route to appropriate pipeline        │   │
│  ├─ Orchestrator Node                      │   │
│  │ ├─ Decompose query into subtasks        │   │
│  │ └─ Create execution plan                │   │
│  ├─ Retriever Node                         │   │
│  │ ├─ Semantic search each subtask         │   │
│  │ └─ Rank by relevance                    │   │
│  ├─ Analyzer Node                          │   │
│  │ ├─ Synthesize across documents          │   │
│  │ └─ Generate reasoning steps             │   │
│  ├─ Verifier Node                          │   │
│  │ ├─ Calculate grounding score            │   │
│  │ └─ Detect hallucinations                │   │
│  └─ Memory Node                             │   │
│     ├─ Update conversation history         │   │
│     └─ Track context                       │   │
└──────────────────┬───────────────────────────────┘
                  │
┌──────────────────▼───────────────────────────────┐
│  Agent Infrastructure Layer                      │
│  ├─ BaseAgent (base_agent.py)                   │
│  ├─ Status tracking                            │
│  ├─ Logging & execution traces                 │
│  └─ Error handling                             │
└──────────────────┬───────────────────────────────┘
                  │
┌──────────────────▼───────────────────────────────┐
│  Data Layer                                      │
│  ├─ DocumentManager (document_manager.py)       │
│  │  ├─ Document ingestion                      │
│  │  ├─ Text chunking                           │
│  │  └─ Vector storage/retrieval                │
│  ├─ Types (types.py)                           │
│  │  ├─ Document, DocumentChunk                 │
│  │  ├─ RetrievalResult                         │
│  │  ├─ AnalysisResult, VerificationResult      │
│  │  └─ AgentMessage, AgentState                │
│  └─ Configuration (settings.py)                │
│     ├─ Thresholds, paths                       │
│     └─ Embeddings model config                 │
└──────────────────┬───────────────────────────────┘
                  │
┌──────────────────▼───────────────────────────────┐
│  Vector Database Layer                           │
│  ├─ Chroma (PersistentClient)                   │
│  ├─ Embeddings: all-MiniLM-L6-v2 (384-dim)      │
│  ├─ Search index: HNSW algorithm                │
│  └─ Storage: data/vector_store/                 │
└──────────────────────────────────────────────────┘
```

### 1. **Router Node** (LangGraph Entry Point)
**File**: `core/langgraph_framework.py`

- **Purpose**: Classify query type and route appropriately
- **Logic**:
  - Detect follow-up questions (check conversation history)
  - Identify simple vs. complex queries
  - Route to orchestrator (default) or memory (follow-ups)

### 2. **Orchestrator Node**
**File**: `core/langgraph_framework.py` (Node in LangGraph)
**Agent**: `agents/orchestrator_agent.py` (Original implementation)

- **Responsibility**: Query decomposition
- **Updates State**: Adds subtasks to AgentState
- **Output**: List of logical subtasks

### 3. **Retriever Node**
**File**: `core/langgraph_framework.py` (Node in LangGraph)
**Agent**: `agents/retriever_agent.py` (Original implementation)

- **Responsibility**: Semantic document search
- **Updates State**: Adds retrieved_documents to AgentState
- **Vector DB**: Chroma with ONNX embeddings
- **Output**: List of RetrievalResult objects

### 4. **Analyzer Node**
**File**: `core/langgraph_framework.py` (Node in LangGraph)
**Agent**: `agents/analyzer_agent.py` (Powered by Google Gemini)

- **Responsibility**: Answer synthesis and reasoning across documents
- **LLM Integration**: Google Gemini API (free tier)
- **Updates State**: Adds analysis_result to AgentState
- **Features**:
  - Sends retrieved documents to Gemini for intelligent synthesis
  - Automatically falls back to template synthesis if Gemini unavailable
  - Extracts reasoning steps and source references
  - Handles multi-document cross-referencing
  
- **Gemini Configuration**:
  - Model: `gemini-pro`
  - Temperature: 0.7 (balanced reasoning)
  - Max tokens: 2048
  - Free tier: 60 requests/min, unlimited daily
  
- **Output**: AnalysisResult with synthesized answer and reasoning

### 5. **Verifier Agent** (`agents/verifier_agent.py`)
**Responsibility**: Validation, Grounding & Guardrails

- **Role**: Ensures quality and trustworthiness
- **Functions**:
  - Verifies grounding (is answer supported by sources?)
  - Detects potential hallucinations
  - Applies safety guardrails
  - Assigns confidence levels
  - Flags potential issues
  
- **Key Metrics**:
  - Grounding Score: 0-1 (higher = better grounded)
  - Hallucination Count
  - Confidence Level: low/medium/high
  - Warning flags and validation notes

### 6. **Memory Agent** (`agents/memory_agent.py`)
**Responsibility**: Context Management & History

- **Role**: Maintains conversation state and context
- **Functions**:
  - Stores conversation history
  - Manages session state
  - Tracks execution traces
  - Enables context reuse across queries
  
- **Features**:
  - Circular buffer for conversation history (max 100 entries)
  - Session state dictionary
  - Execution trace storage

## Data Flow and Workflow

### Query Processing Pipeline

```
1. USER QUERY
   │
   ▼
2. ORCHESTRATOR AGENT
   - Analyze query
   - Create execution plan
   - Route to retriever
   │
   ▼
3. RETRIEVER AGENT
   - Semantic search
   - Rank by relevance
   - Filter results
   │
   ▼
4. ANALYZER AGENT
   - Cross-document reasoning
   - Synthesize answer
   - Extract sources
   │
   ▼
5. VERIFIER AGENT
   - Check grounding
   - Detect hallucinations
   - Assign confidence
   │
   ▼
6. EVALUATION SYSTEM
   - Calculate metrics
   - Log traces
   - Save results
   │
   ▼
7. MEMORY AGENT
   - Store response
   - Update context
   │
   ▼
8. SYSTEM RESPONSE
   - Answer
   - Sources
   - Verification status
   - Evaluation metrics
```

## Core Data Structures

### Key Type Definitions (see `core/types.py`)

1. **Document**: Enterprise document with metadata
2. **DocumentChunk**: Text chunk with embeddings
3. **RetrievalResult**: Search result with relevance score
4. **QueryPlan**: Decomposed query tasks
5. **AnalysisResult**: Reasoning output
6. **VerificationResult**: Validation results
7. **EvaluationMetrics**: System performance metrics
8. **SystemResponse**: Final response to user

## Vector Database

**Type**: Chroma (Chromadb)
**Purpose**: Semantic search and retrieval

- **Persistence**: Local file-based storage in `data/vector_store/`
- **Embedding Model**: text-embedding-3-small (OpenAI)
- **Search Algorithm**: Cosine similarity
- **Features**:
  - Metadata preservation (source, title, chunk index)
  - Persistent storage
  - Efficient semantic search

### Document Ingestion Process

```
Raw Document
    │
    ▼
Load & Read Content
    │
    ▼
Chunk (1000 chars, 200 overlap)
    │
    ▼
Create Embeddings
    │
    ▼
Store in Vector DB with Metadata
    │
    ▼
Persisted to Disk
```

## Evaluation & Observability System

**Location**: `evaluation/evaluation_system.py`

### Evaluation Metrics

1. **Retrieval Relevance Score**
   - Average relevance of retrieved documents
   - Range: 0-1

2. **Grounding Score**
   - How well answer is supported by sources
   - Calculated from document references + relevance

3. **Hallucination Detection**
   - Binary flag
   - Triggered by: unsupported claims, length anomalies

4. **Failure Detection**
   - No documents retrieved
   - Low grounding confidence
   - Hallucinations detected
   - System errors

### Logging & Tracing

- **Execution Traces**: Step-by-step agent decisions
- **Agent Messages**: Communication between agents
- **Evaluation Reports**: Comprehensive assessment
- **Log Files**: Persisted in `logs/` directory
- **Evaluation Files**: JSON output in `evaluation/` directory

## Configuration

**Location**: `config/settings.py`

### Key Parameters

```python
CHUNK_SIZE = 1000              # Characters per chunk
CHUNK_OVERLAP = 200            # Overlap between chunks
TOP_K_RETRIEVAL = 5            # Documents to retrieve
RETRIEVAL_SCORE_THRESHOLD = 0.6 # Minimum relevance score
GROUNDING_THRESHOLD = 0.7      # Minimum grounding score
HALLUCINATION_THRESHOLD = 0.5  # Hallucination detection threshold
```

## Security & Guardrails

### Implemented Safeguards

1. **Input Validation**
   - Empty query rejection
   - Query size limits

2. **Hallucination Control**
   - Source attribution requirement
   - Confidence thresholds
   - Anomaly detection

3. **Grounding Verification**
   - Answer-source alignment check
   - Document reference validation
   - Confidence scoring

4. **Output Governance**
   - Warning flags for low confidence
   - Clear source attribution
   - Explicit uncertainty handling

## Agent Communication

### Message Types

- **QUERY**: User query to orchestrator
- **RETRIEVAL_REQUEST**: Request for document search
- **ANALYSIS_REQUEST**: Request for reasoning
- **VERIFICATION_REQUEST**: Request for validation
- **RESPONSE**: Agent response
- **ERROR**: Error message

### Agent State Machine

```
IDLE → PROCESSING → DONE
              ↓
            ERROR
```

## Usage

### Basic Usage

```python
from core.document_manager import DocumentManager
from core.orchestration import EnterpriseKnowledgeAgent

# Initialize system
doc_manager = DocumentManager()
agent = EnterpriseKnowledgeAgent(doc_manager)

# Ingest documents
agent.ingest_text(document_content, "Document Title")

# Process query
response = await agent.process_query("Your question here")

# Display results
print(agent.format_response(response))
```

### Running the Application

**Interactive Mode** (default):
```bash
python main.py
```

**Demo Mode**:
```bash
python main.py --demo
```

## Performance Characteristics

- **Query Processing Time**: ~2-5 seconds (depending on document size)
- **Memory Usage**: ~500MB for 1000-document collection
- **Retrieval Speed**: <500ms for vector search
- **Throughput**: 100+ queries/hour on standard hardware

## Extension Points

1. **Custom LLM Integration**: Replace orchestrator/analyzer reasoning
2. **Alternative Vector DBs**: Swap Chroma for Pinecone/Weaviate
3. **Enhanced Evaluation**: Add custom metrics/checks
4. **Multi-Language Support**: Add translation layer
5. **UI Layer**: Streamlit/Chainlit frontend

## Error Handling

- Graceful degradation on missing documents
- Detailed error logging
- User-friendly error messages
- System error tracking

## Testing

See `tests/` directory for:
- Unit tests for agents
- Integration tests for workflows
- Evaluation tests for metrics

## Future Enhancements

1. LangGraph integration for advanced workflow orchestration
2. Multi-modal document support (images, tables)
3. Conversation memory across sessions
4. Advanced reasoning with tool use
5. Multi-language document support
6. Real-time document updates
7. User feedback loop integration

---

**Version**: 1.0
**Last Updated**: October 2026
