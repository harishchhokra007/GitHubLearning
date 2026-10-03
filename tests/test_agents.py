"""Unit tests for the Enterprise Knowledge Operations Agent."""

import pytest
import asyncio
from core.types import (
    Document, DocumentChunk, RetrievalResult, QueryPlan, Subtask,
    AnalysisResult, VerificationResult, SystemResponse
)
from agents.orchestrator_agent import OrchestratorAgent
from agents.retriever_agent import RetrieverAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.verifier_agent import VerifierAgent
from agents.memory_agent import MemoryAgent
from agents.base_agent import AgentRegistry
from core.document_manager import DocumentManager, DocumentProcessor
from evaluation.evaluation_system import EvaluationSystem


class TestDocumentStructures:
    """Test core data structures."""
    
    def test_document_creation(self):
        """Test Document creation."""
        doc = Document(
            id="doc1",
            title="Test Document",
            content="This is test content",
            source_path="/path/to/doc.txt"
        )
        assert doc.id == "doc1"
        assert doc.title == "Test Document"
        assert len(doc.chunks) == 0
    
    def test_document_chunk_creation(self):
        """Test DocumentChunk creation."""
        chunk = DocumentChunk(
            id="chunk1",
            document_id="doc1",
            content="Chunk content",
            chunk_index=0
        )
        assert chunk.id == "chunk1"
        assert chunk.document_id == "doc1"
        assert chunk.chunk_index == 0


class TestDocumentProcessor:
    """Test document processing."""
    
    def test_chunk_document(self):
        """Test document chunking."""
        doc = Document(
            id="doc1",
            title="Test",
            content="A" * 2000,  # 2000 characters
            source_path="/test"
        )
        
        processor = DocumentProcessor()
        chunks = processor.chunk_document(doc, chunk_size=1000, overlap=200)
        
        assert len(chunks) > 1
        assert chunks[0].chunk_index == 0
        assert all(c.document_id == "doc1" for c in chunks)


class TestAgents:
    """Test agent functionality."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_agent(self):
        """Test orchestrator query decomposition."""
        agent = OrchestratorAgent()
        result = await agent.process({'query': 'Test query'})
        
        assert result['status'] == 'success'
        assert 'plan' in result
        assert 'subtasks' in result
        assert len(result['subtasks']) > 0
    
    @pytest.mark.asyncio
    async def test_analyzer_agent(self):
        """Test analyzer agent."""
        agent = AnalyzerAgent()
        
        retrieval_results = [
            RetrievalResult(
                document_id="doc1",
                chunk_id="chunk1",
                content="Sample content about testing",
                relevance_score=0.8,
                source="test_doc",
                metadata={}
            )
        ]
        
        result = await agent.process({
            'query': 'What is testing?',
            'retrieval_results': retrieval_results
        })
        
        assert result['status'] == 'success'
        assert 'analysis_result' in result
    
    @pytest.mark.asyncio
    async def test_verifier_agent(self):
        """Test verifier agent."""
        agent = VerifierAgent()
        
        retrieval_results = [
            RetrievalResult(
                document_id="doc1",
                chunk_id="chunk1",
                content="Test content",
                relevance_score=0.9,
                source="test_doc",
                metadata={}
            )
        ]
        
        analysis = AnalysisResult(
            analysis_id="an1",
            query="Test?",
            retrieved_documents=retrieval_results,
            reasoning_steps=["Step 1", "Step 2"],
            synthesized_answer="This is the answer.",
            source_references=[{'source': 'test_doc'}]
        )
        
        result = await agent.process({'analysis_result': analysis})
        
        assert result['status'] == 'success'
        assert 'verification_result' in result


class TestAgentRegistry:
    """Test agent registry."""
    
    def test_agent_registration(self):
        """Test agent registration."""
        registry = AgentRegistry()
        agent = OrchestratorAgent()
        
        registry.register(agent)
        
        assert registry.get_agent("orchestrator_1") == agent
        assert "orchestrator_1" in registry.list_agents()


class TestMemoryAgent:
    """Test memory agent."""
    
    @pytest.mark.asyncio
    async def test_memory_storage(self):
        """Test memory operations."""
        agent = MemoryAgent()
        
        result = await agent.process({
            'operation': 'update_state',
            'state_update': {'key': 'value'}
        })
        
        assert result['status'] == 'success'


class TestEvaluationSystem:
    """Test evaluation system."""
    
    def test_evaluation_metrics(self):
        """Test evaluation metric calculation."""
        eval_system = EvaluationSystem()
        
        sources = [
            RetrievalResult(
                document_id="doc1",
                chunk_id="chunk1",
                content="Content 1",
                relevance_score=0.9,
                source="doc1",
                metadata={}
            ),
            RetrievalResult(
                document_id="doc2",
                chunk_id="chunk2",
                content="Content 2",
                relevance_score=0.8,
                source="doc2",
                metadata={}
            )
        ]
        
        relevance = eval_system._evaluate_retrieval_relevance(sources)
        assert 0 <= relevance <= 1
        assert relevance > 0.8


class TestDocumentManager:
    """Test document manager."""
    
    def test_document_manager_initialization(self):
        """Test manager initialization."""
        manager = DocumentManager()
        assert manager.vector_db is not None
        assert manager.processor is not None
    
    def test_text_ingestion(self):
        """Test text document ingestion."""
        manager = DocumentManager()
        doc = manager.ingest_text("Test content here", "Test Doc")
        
        assert doc.id is not None
        assert doc.title == "Test Doc"
        assert len(doc.chunks) > 0


# Integration Tests
class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow."""
        # Initialize
        doc_manager = DocumentManager()
        doc_manager.ingest_text("Company policy: Be professional and respectful", "Policy")
        
        # Create agents
        orchestrator = OrchestratorAgent()
        retriever = RetrieverAgent(doc_manager)
        analyzer = AnalyzerAgent()
        verifier = VerifierAgent()
        
        # Process query
        query = "What is the company policy?"
        
        # Step 1: Plan
        plan_result = await orchestrator.process({'query': query})
        assert plan_result['status'] == 'success'
        
        # Step 2: Retrieve
        retrieval_result = await retriever.process({
            'query': query,
            'top_k': 3
        })
        assert retrieval_result['status'] == 'success'
        
        # Step 3: Analyze
        analysis_result = await analyzer.process({
            'query': query,
            'retrieval_results': retrieval_result['retrieval_results']
        })
        assert analysis_result['status'] == 'success'
        
        # Step 4: Verify
        verification_result = await verifier.process({
            'analysis_result': analysis_result['analysis_result']
        })
        assert verification_result['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
