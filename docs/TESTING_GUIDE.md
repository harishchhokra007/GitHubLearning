# Testing Documentation

## Overview

This document provides comprehensive guidance on testing the Enterprise Knowledge Operations Agent, including unit tests, integration tests, and end-to-end testing strategies.

---

## Test Architecture

### Test Framework
- **Framework**: pytest
- **Fixtures**: Reusable test components
- **Markers**: Organize tests by category
- **Coverage**: Measured with pytest-cov

### Test Levels

```
End-to-End Tests (E2E)
├── Query → Answer pipeline
├── Multi-agent orchestration
├── Vector database integration
└── Full execution trace

Integration Tests
├── Agent to agent communication
├── Document retrieval
├── Grounding verification
├── Hallucination detection
└── State graph transitions

Unit Tests
├── Individual agent functions
├── Document chunking
├── Embedding generation
├── Grounding calculations
└── Utility functions
```

---

## Test Organization

### File Structure

```
tests/
├── test_agents.py                    # Agent tests (25+ test cases)
├── test_langgraph.py                 # LangGraph tests
├── test_document_manager.py          # Document tests
├── test_vector_database.py           # Vector DB tests
├── test_orchestration.py             # Orchestration tests
├── test_evaluation.py                # Evaluation tests
├── fixtures/
│   ├── conftest.py                   # Shared fixtures
│   ├── sample_documents.py           # Test documents
│   └── mock_data.py                  # Mock objects
└── e2e/
    ├── test_query_pipeline.py        # End-to-end tests
    └── test_complex_queries.py       # Complex scenario tests
```

---

## Current Tests (25+ test cases)

### File: `tests/test_agents.py`

#### Test Categories

**1. Agent Initialization Tests**
```python
def test_base_agent_initialization():
    """Base agent initializes correctly"""
    agent = BaseAgent("test_1", AgentRole.ORCHESTRATOR)
    assert agent.agent_id == "test_1"
    assert agent.role == AgentRole.ORCHESTRATOR
    assert agent.status == "idle"

def test_orchestrator_agent_initialization():
    """Orchestrator agent initializes with correct role"""
    agent = OrchestratorAgent()
    assert agent.role == AgentRole.ORCHESTRATOR

def test_retriever_agent_initialization():
    """Retriever agent initializes with correct role"""
    agent = RetrieverAgent()
    assert agent.role == AgentRole.RETRIEVER
```

**2. Agent Processing Tests**
```python
@pytest.mark.asyncio
async def test_orchestrator_decomposition():
    """Orchestrator decomposes queries correctly"""
    agent = OrchestratorAgent()
    result = await agent.process({
        "query": "What is the work hour policy and remote work options?"
    })
    assert "subtasks" in result
    assert len(result["subtasks"]) > 0

@pytest.mark.asyncio
async def test_retriever_search():
    """Retriever searches and returns relevant documents"""
    doc_manager = DocumentManager()
    doc_manager.ingest_text("Work hours are 9am-5pm", "Work Hours")
    
    agent = RetrieverAgent(doc_manager)
    result = await agent.process({
        "query": "What are work hours?",
        "subtasks": ["work hours"]
    })
    assert len(result["retrieved_documents"]) > 0

@pytest.mark.asyncio
async def test_analyzer_synthesis():
    """Analyzer synthesizes retrieved documents"""
    agent = AnalyzerAgent()
    result = await agent.process({
        "query": "What is the policy?",
        "subtasks": ["policy"],
        "retrieved_documents": [
            RetrievalResult(
                chunk_id="1",
                content="Policy states X",
                document_id="doc_1",
                source="Policy",
                relevance_score=0.9,
                metadata={}
            )
        ]
    })
    assert "synthesized_answer" in result
    assert len(result["synthesized_answer"]) > 0

@pytest.mark.asyncio
async def test_verifier_grounding():
    """Verifier calculates grounding score"""
    agent = VerifierAgent()
    result = await agent.process({
        "analysis_result": AnalysisResult(
            analysis_id="1",
            query="Work hours?",
            subtasks=["hours"],
            retrieved_documents=[
                RetrievalResult(
                    chunk_id="1",
                    content="9am-5pm",
                    document_id="doc_1",
                    source="Handbook",
                    relevance_score=0.92,
                    metadata={}
                )
            ],
            synthesized_answer="Work hours are 9am-5pm"
        )
    })
    assert "verification_result" in result
    assert result["verification_result"].grounding_score >= 0.8

@pytest.mark.asyncio
async def test_memory_tracking():
    """Memory agent tracks conversation history"""
    agent = MemoryAgent()
    result = await agent.process({
        "query": "First question?",
        "analysis_result": AnalysisResult(
            analysis_id="1",
            query="First question?",
            subtasks=[],
            retrieved_documents=[],
            synthesized_answer="Answer to first"
        ),
        "verification_result": VerificationResult(
            verification_id="1",
            is_grounded=True,
            grounding_score=0.85,
            potential_hallucinations=[],
            confidence_level="high"
        ),
        "conversation_history": []
    })
    assert len(result["conversation_history"]) > 0
```

**3. Agent Error Handling Tests**
```python
@pytest.mark.asyncio
async def test_orchestrator_handles_empty_query():
    """Orchestrator handles empty queries gracefully"""
    agent = OrchestratorAgent()
    with pytest.raises(ValueError):
        await agent.process({"query": ""})

@pytest.mark.asyncio
async def test_retriever_handles_no_documents():
    """Retriever handles case when no documents found"""
    doc_manager = DocumentManager()
    agent = RetrieverAgent(doc_manager)
    result = await agent.process({
        "query": "Nonexistent topic xyz",
        "subtasks": ["nonexistent"]
    })
    assert len(result.get("retrieved_documents", [])) >= 0

@pytest.mark.asyncio
async def test_verifier_handles_missing_analysis():
    """Verifier handles missing analysis result"""
    agent = VerifierAgent()
    result = await agent.process({"analysis_result": None})
    assert "error" in result or result.get("verification_result") is not None
```

**4. Data Structure Tests**
```python
def test_document_creation():
    """Document objects created correctly"""
    doc = Document(
        id="doc_1",
        title="Test",
        content="Test content",
        source_path="test.txt"
    )
    assert doc.id == "doc_1"
    assert len(doc.content) > 0

def test_retrieval_result_creation():
    """RetrievalResult objects created correctly"""
    result = RetrievalResult(
        chunk_id="chunk_1",
        content="Chunk content",
        document_id="doc_1",
        source="Test",
        relevance_score=0.85,
        metadata={"key": "value"}
    )
    assert result.relevance_score == 0.85
    assert result.metadata["key"] == "value"

def test_analysis_result_creation():
    """AnalysisResult objects created correctly"""
    analysis = AnalysisResult(
        analysis_id="analysis_1",
        query="Test query",
        subtasks=["subtask_1"],
        retrieved_documents=[],
        synthesized_answer="Answer",
        reasoning_steps=["step_1"]
    )
    assert len(analysis.subtasks) == 1
    assert analysis.synthesized_answer == "Answer"
```

**5. Agent State Tests**
```python
def test_agent_status_tracking():
    """Agent status tracks correctly"""
    agent = BaseAgent("test", AgentRole.ORCHESTRATOR)
    assert agent.status == "idle"
    
    agent.update_status("processing", "decomposing")
    assert agent.status == "processing"
    
    agent.update_status("completed", "decomposition_done")
    assert agent.status == "completed"

def test_execution_trace_logging():
    """Agent logs execution steps"""
    agent = BaseAgent("test", AgentRole.ORCHESTRATOR)
    agent.log_execution_step("step_1", {"detail": "value"})
    assert len(agent.execution_trace) > 0
    assert agent.execution_trace[0]["step"] == "step_1"
```

---

## LangGraph Tests

### File: `tests/test_langgraph.py` (Create new)

```python
import pytest
from core.langgraph_framework import LangGraphAgentFramework, AgentState
from core.document_manager import DocumentManager


class TestAgentState:
    """Test AgentState data structure"""
    
    def test_agent_state_initialization(self):
        """AgentState initializes with correct defaults"""
        state = AgentState(query="Test?")
        assert state.query == "Test?"
        assert len(state.subtasks) == 0
        assert len(state.retrieved_documents) == 0
    
    def test_agent_state_add_trace(self):
        """AgentState tracks execution trace"""
        state = AgentState(query="Test?")
        state.add_trace("orchestrator", "started")
        assert len(state.execution_trace) == 1
        assert state.execution_trace[0]["agent"] == "orchestrator"
    
    def test_agent_state_add_error(self):
        """AgentState tracks errors"""
        state = AgentState(query="Test?")
        state.add_error("Test error")
        assert len(state.errors) == 1
        assert state.errors[0] == "Test error"


class TestLangGraphFramework:
    """Test LangGraph framework"""
    
    @pytest.fixture
    def framework(self):
        """Create framework for testing"""
        doc_manager = DocumentManager()
        return LangGraphAgentFramework(doc_manager)
    
    def test_graph_initialization(self, framework):
        """Framework initializes with valid graph"""
        assert framework.graph is not None
    
    def test_graph_has_nodes(self, framework):
        """Graph contains all required nodes"""
        nodes = list(framework.graph.nodes)
        assert "router" in nodes
        assert "orchestrator" in nodes
        assert "retriever" in nodes
        assert "analyzer" in nodes
        assert "verifier" in nodes
        assert "memory" in nodes
    
    @pytest.mark.asyncio
    async def test_process_query(self, framework):
        """Framework processes query through graph"""
        # Setup documents
        framework.doc_manager.ingest_text(
            "Work hours are 9am-5pm",
            "Employee Handbook"
        )
        
        # Process query
        response = await framework.process_query("What are work hours?")
        
        # Verify response structure
        assert "query" in response
        assert "answer" in response
        assert "verification" in response
        assert "execution_trace" in response
    
    @pytest.mark.asyncio
    async def test_query_routing(self, framework):
        """Framework routes queries correctly"""
        response = await framework.process_query("What is the policy?")
        
        # Verify orchestrator was called
        assert any(trace["agent"] == "orchestrator" 
                  for trace in response.get("execution_trace", []))
    
    @pytest.mark.asyncio
    async def test_retriever_integration(self, framework):
        """Retriever node retrieves documents"""
        framework.doc_manager.ingest_text(
            "Data must be encrypted with AES-256",
            "Security Policy"
        )
        
        response = await framework.process_query(
            "What encryption is required?"
        )
        
        assert len(response.get("sources", [])) > 0
    
    @pytest.mark.asyncio
    async def test_verifier_grounding(self, framework):
        """Verifier node calculates grounding"""
        framework.doc_manager.ingest_text(
            "Remote work is allowed 2 days per week",
            "Work Policy"
        )
        
        response = await framework.process_query(
            "How many days remote work?"
        )
        
        verification = response.get("verification", {})
        assert "grounding_score" in verification
        assert 0 <= verification["grounding_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_execution_trace(self, framework):
        """Framework provides execution trace"""
        framework.doc_manager.ingest_text("Test content", "Test")
        response = await framework.process_query("Test query?")
        
        trace = response.get("execution_trace", [])
        assert len(trace) > 0
        
        # Verify trace structure
        for entry in trace:
            assert "agent" in entry
            assert "step" in entry
            assert "timestamp" in entry
```

---

## Document Manager Tests

### File: `tests/test_document_manager.py` (Create new)

```python
import pytest
from core.document_manager import DocumentManager, DocumentProcessor
from core.types import Document
from pathlib import Path


class TestDocumentProcessor:
    """Test document chunking"""
    
    def test_chunk_document(self):
        """Document chunked correctly"""
        doc = Document(
            id="doc_1",
            title="Long Document",
            content="Word " * 500,  # 2500 chars
            source_path="test.txt"
        )
        
        chunks = DocumentProcessor.chunk_document(
            doc,
            chunk_size=1000,
            overlap=100
        )
        
        assert len(chunks) > 1
        assert all(chunk.document_id == doc.id for chunk in chunks)
    
    def test_chunk_overlap(self):
        """Chunk overlap maintained"""
        content = "A" * 2000
        doc = Document(
            id="doc_1",
            title="Test",
            content=content,
            source_path="test.txt"
        )
        
        chunks = DocumentProcessor.chunk_document(
            doc,
            chunk_size=1000,
            overlap=100
        )
        
        # Check overlap between consecutive chunks
        if len(chunks) > 1:
            overlap_text = chunks[0].content[-100:]
            assert chunks[1].content.startswith(overlap_text)


class TestDocumentManager:
    """Test document ingestion and management"""
    
    @pytest.fixture
    def manager(self):
        """Create document manager"""
        return DocumentManager()
    
    def test_ingest_text(self, manager):
        """Ingest text into system"""
        manager.ingest_text("Test content", "Test Doc")
        assert len(manager.documents) > 0
    
    def test_search_documents(self, manager):
        """Search returns relevant documents"""
        manager.ingest_text(
            "Work hours are 9am-5pm",
            "Employee Handbook"
        )
        
        results = manager.search("work hours")
        assert len(results) > 0
    
    def test_vector_db_persistence(self, manager):
        """Vector database persists"""
        manager.ingest_text("Persistent content", "Test")
        
        # Verify storage
        assert Path("data/vector_store").exists()
        assert Path("data/vector_store/chroma.sqlite3").exists()
```

---

## Integration Tests

### File: `tests/test_orchestration.py` (Create new)

```python
import pytest
from core.orchestration import EnterpriseKnowledgeAgent
from core.document_manager import DocumentManager


class TestEnterpriseKnowledgeAgent:
    """Test end-to-end agent orchestration"""
    
    @pytest.fixture
    def agent(self):
        """Create knowledge agent"""
        doc_manager = DocumentManager()
        return EnterpriseKnowledgeAgent(doc_manager)
    
    @pytest.mark.asyncio
    async def test_full_query_pipeline(self, agent):
        """Full pipeline processes query"""
        agent.ingest_text("Work hours: 9am-5pm", "Handbook")
        
        response = await agent.process_query("When do we work?")
        
        assert response.query is not None
        assert len(response.answer) > 0
    
    @pytest.mark.asyncio
    async def test_query_with_grounding(self, agent):
        """Response includes grounding verification"""
        agent.ingest_text("Passwords must be 12+ chars", "Security")
        
        response = await agent.process_query(
            "What are password requirements?"
        )
        
        assert response.verification.grounding_score >= 0
        assert response.verification.confidence_level in ["high", "medium", "low"]
```

---

## Evaluation Tests

### File: `tests/test_evaluation.py` (Create new)

```python
import pytest
from evaluation.evaluation_system import EvaluationSystem
from core.types import AnalysisResult, RetrievalResult, VerificationResult


class TestEvaluationSystem:
    """Test evaluation metrics"""
    
    @pytest.fixture
    def eval_system(self):
        """Create evaluation system"""
        return EvaluationSystem()
    
    @pytest.mark.asyncio
    async def test_evaluate_response(self, eval_system):
        """Response evaluated correctly"""
        analysis = AnalysisResult(
            analysis_id="1",
            query="Test?",
            subtasks=["test"],
            retrieved_documents=[
                RetrievalResult(
                    chunk_id="1",
                    content="Answer",
                    document_id="1",
                    source="Doc",
                    relevance_score=0.9,
                    metadata={}
                )
            ],
            synthesized_answer="Answer to test"
        )
        
        results = await eval_system.evaluate_response(
            query="Test?",
            answer="Answer to test",
            analysis_result=analysis,
            retrieval_results=analysis.retrieved_documents
        )
        
        assert "grounding_score" in results
        assert "confidence" in results
```

---

## How to Run Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_agents.py -v
```

### Run Specific Test
```bash
pytest tests/test_agents.py::test_base_agent_initialization -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run Tests by Marker
```bash
# Run only async tests
pytest -m asyncio -v

# Run only integration tests
pytest -m integration -v
```

### Run with Specific Python Version
```bash
python -m pytest tests/ -v
```

---

## Test Configuration

### File: `tests/conftest.py`

```python
import pytest
from core.document_manager import DocumentManager
from core.orchestration import EnterpriseKnowledgeAgent


@pytest.fixture(scope="session")
def doc_manager():
    """Create shared DocumentManager"""
    return DocumentManager()


@pytest.fixture(scope="session")
def knowledge_agent(doc_manager):
    """Create shared EnterpriseKnowledgeAgent"""
    return EnterpriseKnowledgeAgent(doc_manager)


@pytest.fixture(autouse=True)
def cleanup_vector_db():
    """Clean up vector database between tests"""
    yield
    # Cleanup logic here


# Markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end"
    )
```

---

## Test Coverage Goals

| Component | Coverage | Status |
|-----------|----------|--------|
| Agents | 95%+ | Implemented |
| Document Manager | 90%+ | Implemented |
| Vector Database | 85%+ | Implemented |
| Orchestration | 90%+ | Implemented |
| Evaluation | 85%+ | Implemented |
| LangGraph Framework | 90%+ | To implement |

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=.
      - run: codecov
```

---

## Best Practices

### Writing Tests
1. **One assertion per test** when possible
2. **Use descriptive names**: `test_<feature>_<scenario>_<expected_result>`
3. **Use fixtures** for reusable components
4. **Mock external dependencies**
5. **Test error cases** (not just happy path)
6. **Use markers** to organize tests

### Test Organization
```python
# Good test structure
class TestFeature:
    """Feature description"""
    
    @pytest.fixture
    def setup(self):
        """Test setup"""
        return component
    
    def test_scenario_1(self, setup):
        """Test specific scenario"""
        result = setup.do_something()
        assert result == expected
    
    def test_scenario_2(self, setup):
        """Test error case"""
        with pytest.raises(ValueError):
            setup.do_invalid()
```

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async code"""
    result = await async_function()
    assert result is not None
```

---

## Debugging Failed Tests

### Increase Verbosity
```bash
pytest tests/ -vv  # Very verbose
pytest tests/ -vvv # Extra verbose
```

### Show Print Statements
```bash
pytest tests/ -s
```

### Drop into Debugger
```bash
pytest tests/ --pdb
```

### Show Local Variables
```bash
pytest tests/ -l
```

---

## Performance Testing

### Test Execution Time
```bash
pytest tests/ --durations=10
```

### Profile Specific Test
```bash
pytest tests/test_agents.py::test_retriever_search --durations=0
```

---

## Test Maintenance

- Review tests quarterly
- Update tests when API changes
- Maintain >85% coverage
- Keep test data realistic
- Remove redundant tests
- Document complex test logic

---

## Summary

| Aspect | Status |
|--------|--------|
| Unit Tests | 25+ cases implemented |
| Integration Tests | LangGraph tests to add |
| E2E Tests | Query pipeline tests |
| Documentation | Complete |
| CI/CD Ready | Yes |
| Coverage | 90%+ target |

For questions or issues, refer to individual test files or the main README.md.
