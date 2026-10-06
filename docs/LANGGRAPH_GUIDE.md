# LangGraph Implementation Guide

## Overview

This project uses **LangGraph** for agentic framework orchestration. LangGraph provides a state graph-based architecture for reliable, observable multi-agent systems.

---

## What is LangGraph?

LangGraph is a library for building stateful, multi-actor applications with LLMs. It provides:

- **StateGraph**: Defined states that flow through nodes
- **Nodes**: Processing steps (agents)
- **Edges**: Transitions between nodes
- **State Persistence**: All state visible at each step
- **Error Handling**: Graceful error propagation

---

## Project Architecture

### Core Files

| File | Purpose |
|------|---------|
| `core/langgraph_framework.py` | LangGraph StateGraph definition |
| `core/orchestration.py` | High-level query orchestration |
| `agents/*.py` | Individual agent implementations |
| `core/document_manager.py` | Document storage/retrieval |

### State Flow

```
User Query
    ↓
[AgentState Created]
    ↓
Router Node → Route query type
    ↓
Orchestrator Node → Decompose into subtasks
    ↓
Retriever Node → Search documents
    ↓
Analyzer Node → Synthesize answer
    ↓
Verifier Node → Validate grounding
    ↓
Memory Node → Store history
    ↓
[Return Final State with Response]
```

---

## AgentState - The Shared State

All agents access and update the same `AgentState`:

```python
@dataclass
class AgentState:
    """Shared state for all agents in the LangGraph"""
    
    # Input
    query: str
    
    # Processing
    subtasks: List[str]
    retrieved_documents: List[RetrievalResult]
    analysis_result: Optional[AnalysisResult]
    verification_result: Optional[VerificationResult]
    
    # History
    conversation_history: List[Dict]
    
    # Observability
    execution_trace: List[Dict]
    
    # Metadata
    started_at: datetime
    completed_at: datetime
```

### Key Benefits of Shared State

1. **Transparency**: Every agent can see previous results
2. **Context**: Full conversation history available
3. **Debugging**: Execution trace at each step
4. **Error Handling**: Errors recorded in state
5. **Verification**: Easy to validate agent outputs

---

## Building the Graph

### Graph Definition

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", router_node_function)
workflow.add_node("orchestrator", orchestrator_node_function)
workflow.add_node("retriever", retriever_node_function)
workflow.add_node("analyzer", analyzer_node_function)
workflow.add_node("verifier", verifier_node_function)
workflow.add_node("memory", memory_node_function)

# Set entry point
workflow.set_entry_point("router")

# Add edges (transitions)
workflow.add_edge("router", "orchestrator")  # Unconditional edge
workflow.add_conditional_edges(
    "router",
    route_function,  # Decides next node
    {"path1": "node1", "path2": "node2"}
)

# Compile
graph = workflow.compile()
```

### Node Functions

Each node is a function that:
1. Receives current state
2. Processes it
3. Updates and returns state

```python
def orchestrator_node(state: AgentState) -> AgentState:
    """Orchestrator processes state and returns updated state"""
    
    # Read from state
    query = state.query
    
    # Process
    subtasks = decompose_query(query)
    
    # Update state
    state.subtasks = subtasks
    state.add_trace("orchestrator", "decomposed", {
        "num_subtasks": len(subtasks)
    })
    
    # Return updated state
    return state
```

---

## Nodes in This Project

### 1. Router Node

**Purpose**: Classify and route query

**Logic**:
```python
def _route_logic(state: AgentState) -> str:
    if is_followup_question(state.query, state.conversation_history):
        return "memory"  # Follow-up → Memory
    else:
        return "orchestrator"  # New query → Orchestrator
```

**Transitions**:
- → memory (if follow-up)
- → orchestrator (if new query)
- → END (if simple)

### 2. Orchestrator Node

**Purpose**: Decompose query into subtasks

**Updates State**:
- `state.subtasks` ← List of subtasks
- `state.execution_trace` ← Append step

**Next**: → Retriever

### 3. Retriever Node

**Purpose**: Search vector database for documents

**Process**:
```
For each subtask:
  1. Generate query embedding (384-dim)
  2. Search Chroma with cosine similarity
  3. Get top 5 similar chunks
  4. Calculate relevance scores
  5. Add to results
```

**Updates State**:
- `state.retrieved_documents` ← List of RetrievalResult

**Next**: → Analyzer

### 4. Analyzer Node

**Purpose**: Synthesize answer from documents

**Process**:
```
1. Group retrieved chunks by source
2. For each source:
   - Extract key information
   - Build answer section
3. Combine into comprehensive answer
4. Generate reasoning steps
```

**Updates State**:
- `state.analysis_result` ← AnalysisResult object

**Next**: → Verifier

### 5. Verifier Node

**Purpose**: Validate answer grounding

**Checks**:
1. **Grounding Score**: How well answer is supported
   ```
   avg_relevance = mean(doc.relevance_score)
   if avg_relevance >= 0.5:
       grounding_score = 0.8 + (avg_relevance * 0.2)
   ```

2. **Hallucination Detection**: Check for unsupported claims
   ```
   if len(answer) > len(sources) * 3:
       flag_hallucination()
   ```

3. **Confidence Level**:
   - high: grounding ≥ 0.8 && no hallucinations
   - medium: grounding ≥ 0.6 && ≤1 hallucination
   - low: otherwise

**Updates State**:
- `state.verification_result` ← VerificationResult

**Next**: → Memory

### 6. Memory Node

**Purpose**: Store conversation history

**Actions**:
1. Add query + answer to history
2. Record grounding score
3. Store confidence level
4. Record timestamp

**Updates State**:
- `state.conversation_history` ← Append new entry

**Next**: → END

---

## Running Queries Through the Graph

### Basic Usage

```python
from core.langgraph_framework import LangGraphAgentFramework
from core.document_manager import DocumentManager

# Initialize
doc_manager = DocumentManager()
framework = LangGraphAgentFramework(doc_manager)

# Ingest documents
framework.doc_manager.ingest_text(
    "Work hours are 9am-5pm",
    "Employee Handbook"
)

# Process query
response = await framework.process_query(
    "What are the work hour policies?"
)

# Response structure
{
    "query": "What are the work hour policies?",
    "answer": "...",
    "sources": [...],
    "verification": {
        "grounded": True,
        "grounding_score": 0.92,
        "confidence": "high",
        "hallucinations": []
    },
    "execution_trace": [
        {"agent": "router", "step": "query_received", ...},
        {"agent": "orchestrator", "step": "decomposed", ...},
        ...
    ],
    "execution_time_ms": 210.5
}
```

---

## Execution Trace Example

```python
execution_trace = [
    {
        "agent": "router",
        "step": "query_received",
        "timestamp": "2026-10-05T22:30:00Z",
        "details": {"query": "What are work hours?"}
    },
    {
        "agent": "orchestrator",
        "step": "decomposed",
        "timestamp": "2026-10-05T22:30:01Z",
        "details": {
            "num_subtasks": 3,
            "subtasks": ["work hours", "remote work", "time off"]
        }
    },
    {
        "agent": "retriever",
        "step": "completed",
        "timestamp": "2026-10-05T22:30:02Z",
        "details": {
            "num_documents": 3,
            "avg_relevance": 0.87
        }
    },
    {
        "agent": "analyzer",
        "step": "completed",
        "timestamp": "2026-10-05T22:30:03Z",
        "details": {
            "answer_length": 250,
            "num_sources": 1
        }
    },
    {
        "agent": "verifier",
        "step": "completed",
        "timestamp": "2026-10-05T22:30:03Z",
        "details": {
            "grounding_score": 0.92,
            "confidence": "high"
        }
    }
]
```

---

## Error Handling

Errors are captured in state and propagated gracefully:

```python
# In any node
try:
    result = some_operation()
except Exception as e:
    state.add_error(f"Operation failed: {e}")
    logger.error(f"Error in {agent_name}: {e}")
    # State passed to next node with error recorded
    return state
```

---

## Testing LangGraph

### Unit Test Example

```python
@pytest.mark.asyncio
async def test_process_query():
    """Test full graph execution"""
    doc_manager = DocumentManager()
    framework = LangGraphAgentFramework(doc_manager)
    
    # Setup
    framework.doc_manager.ingest_text("Content", "Source")
    
    # Execute
    response = await framework.process_query("Question?")
    
    # Verify
    assert response["query"] == "Question?"
    assert len(response["answer"]) > 0
    assert response["verification"]["grounding_score"] > 0
```

See `docs/TESTING_GUIDE.md` for comprehensive testing guidance.

---

## Extending the Graph

### Adding a New Node

1. **Create the node function**:
```python
def custom_node(state: AgentState) -> AgentState:
    # Process state
    state.custom_field = compute_something()
    state.add_trace("custom", "processed")
    return state
```

2. **Add to graph**:
```python
workflow.add_node("custom", custom_node)
workflow.add_edge("previous_node", "custom")
workflow.add_edge("custom", "next_node")
```

3. **Update orchestration**:
```python
# Test the new node
response = await framework.process_query("test query")
assert "custom" in response["execution_trace"]
```

---

## Performance Considerations

### Execution Time Breakdown

Typical query (210ms):
- Router: 1ms
- Orchestrator: 2ms
- Retriever: 80ms (vector search)
- Analyzer: 60ms (synthesis)
- Verifier: 40ms (verification)
- Memory: 20ms (history)
- Overhead: 7ms

### Optimization Tips

1. **Cache embeddings**: Reuse for common queries
2. **Batch retrievals**: Process multiple subtasks together
3. **Parallel nodes**: Use LangGraph's parallel processing
4. **Lazy loading**: Load documents on demand

---

## Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect State at Each Node

```python
def debug_node(state: AgentState) -> AgentState:
    print(f"Current state: {state}")
    print(f"Execution trace: {state.execution_trace}")
    print(f"Errors: {state.errors}")
    return state
```

### Print Execution Trace

```python
response = await framework.process_query("Query?")
for entry in response["execution_trace"]:
    print(f"{entry['agent']}: {entry['step']}")
```

---

## Summary

LangGraph provides:
- ✓ State-based agent orchestration
- ✓ Clear agent responsibilities via nodes
- ✓ Full observability via execution traces
- ✓ Reliable error handling
- ✓ Easy testing and debugging
- ✓ Extensible architecture

**File Reference**: `core/langgraph_framework.py`
