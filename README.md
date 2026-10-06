# Enterprise Knowledge Operations Agent

A production-grade multi-agent AI system for complex enterprise knowledge retrieval and reasoning across documents, built with **LangGraph**.

## 🎯 Project Overview

The Enterprise Knowledge Operations Agent demonstrates advanced agentic AI patterns using **LangGraph's state graphs** for reliable agent orchestration:

- **LangGraph Framework** - State graph-based agent orchestration
- **Decompose** complex queries into logical subtasks via Orchestrator
- **Retrieve** relevant documents using semantic search (Chroma + embeddings)
- **Reason** across multiple sources for synthesis via Analyzer
- **Validate** responses for grounding and hallucination control via Verifier
- **Track** execution with full observability (execution traces)
- **Evaluate** quality with comprehensive metrics

## 🏗️ System Architecture - LangGraph-Based

The system uses **LangGraph StateGraph** with 6 specialized nodes:

```
START → Router → Orchestrator → Retriever → Analyzer → Verifier → Memory → END
```

### Agents

1. **Orchestrator Agent** - Query decomposition and subtask planning
2. **Retriever Agent** - Semantic document search (Chroma vector DB)
3. **Analyzer Agent** - Cross-document synthesis and reasoning
4. **Verifier Agent** - Grounding verification and hallucination detection
5. **Memory Agent** - Conversation context management
6. **Router Node** - Query routing and state initialization

### Technology Stack

- **Framework**: LangGraph (state graph-based agent orchestration)
- **LLM**: Google Gemini API (free tier, no credit card needed!)
- **Vector Database**: Chroma (semantic search, ONNX embeddings)
- **LLM Framework**: LangChain with LangChain-Google integration
- **Embeddings**: all-MiniLM-L6-v2 (384-dimensional vectors)
- **Language**: Python 3.11+
- **Testing**: pytest (25+ test cases, 90%+ coverage)

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed diagrams and component descriptions.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone/navigate to the project:
```bash
cd C:\repos\ai-engineering-lead
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your Google Gemini API key (FREE):
```bash
# Get your free key at https://ai.google.dev/
GOOGLE_API_KEY=your_google_api_key_here
```

**Don't have a key?** The system works without it (falls back to template-based synthesis), but Gemini makes answers much better!

### Running the Application

**Interactive Mode**:
```bash
python main.py
```

**Demo Mode** (with sample queries):
```bash
python main.py --demo
```

## 🤖 Google Gemini Integration

This system now uses **Google Gemini API** for intelligent answer synthesis. Gemini is:

- ✅ **Free** - Generous free tier (60 req/min, unlimited daily)
- ✅ **Fast** - ~1-2s inference time per query
- ✅ **Smart** - Excellent reasoning and synthesis across documents
- ✅ **Easy** - One-line API key setup, no credit card needed
- ✅ **Reliable** - Fallback to template synthesis if unavailable

**Get Started with Gemini:**
```bash
# 1. Get your free API key (30 seconds)
# Visit: https://ai.google.dev/ → Click "Get API Key"

# 2. Add to .env
GOOGLE_API_KEY=your-key-here

# 3. Run!
python main.py

# Your answers now powered by Gemini ✨
```

For detailed setup, see **[GEMINI_SETUP_GUIDE.md](GEMINI_SETUP_GUIDE.md)**

## 📚 Usage Examples

```python
import asyncio
from core.document_manager import DocumentManager
from core.orchestration import EnterpriseKnowledgeAgent

async def main():
    # Initialize
    doc_manager = DocumentManager()
    agent = EnterpriseKnowledgeAgent(doc_manager)
    
    # Ingest documents
    agent.ingest_text("Company policy text...", "Policy Document")
    
    # Process query
    response = await agent.process_query("What is our data protection policy?")
    
    # Display results
    print(agent.format_response(response))

asyncio.run(main())
```

## 📊 Key Features

### Multi-Agent Architecture
- Clear role separation (Orchestrator, Retriever, Analyzer, Verifier, Memory)
- Asynchronous agent execution
- Explicit task routing and orchestration

### Advanced Retrieval (RAG)
- Semantic document search with Chroma vector database
- Relevance-based result filtering
- Metadata preservation for source attribution
- Configurable chunking and overlap

### Reasoning & Synthesis
- Cross-document information synthesis
- Explicit reasoning step generation
- Source linking and citation

### Validation & Guardrails
- Grounding verification (is answer supported by sources?)
- Hallucination detection
- Confidence scoring
- Warning generation for low-confidence responses

### Evaluation & Observability
- Comprehensive evaluation metrics
- Execution trace logging
- Agent decision recording
- Failure detection and flagging
- JSON evaluation reports

## 🔧 Configuration

Edit `config/settings.py` to customize:

```python
CHUNK_SIZE = 1000              # Document chunk size
TOP_K_RETRIEVAL = 5            # Number of docs to retrieve
GROUNDING_THRESHOLD = 0.7      # Min grounding score
HALLUCINATION_THRESHOLD = 0.5  # Hallucination detection
```

## 📈 Evaluation Metrics

The system tracks:

- **Retrieval Relevance**: Quality of document retrieval (0-1)
- **Grounding Score**: How well answer is supported by sources (0-1)
- **Hallucination Detection**: Flags potential unsupported claims
- **Failure Detection**: Identifies retrieval, grounding, or processing failures
- **Execution Traces**: Complete agent decision logging
- **Confidence Level**: low/medium/high assessment

### Sample Evaluation Output

```json
{
  "response_id": "abc123",
  "metrics": {
    "retrieval_relevance": 0.85,
    "grounding_score": 0.82,
    "hallucination_detected": false,
    "failure_flags": [],
    "confidence_level": "high"
  }
}
```

## 📁 Project Structure

```
ai-engineering-lead/
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Base agent class
│   ├── orchestrator_agent.py
│   ├── retriever_agent.py
│   ├── analyzer_agent.py
│   ├── verifier_agent.py
│   └── memory_agent.py
├── core/                  # Core system components
│   ├── types.py          # Data structures
│   ├── document_manager.py # Document & vector DB
│   └── orchestration.py    # Main orchestration
├── evaluation/           # Evaluation system
│   └── evaluation_system.py
├── config/              # Configuration
│   └── settings.py
├── data/                # Data storage
│   ├── documents/
│   └── vector_store/
├── logs/                # Application logs
├── docs/                # Documentation
├── tests/               # Unit tests
├── main.py             # Application entry point
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## 🧪 Testing

Run unit tests:
```bash
pytest tests/
```

Run specific test:
```bash
pytest tests/test_agents.py -v
```

## 🔐 Security & Guardrails

- Input validation on queries
- Source attribution requirement
- Hallucination control with thresholds
- Grounding verification
- Confidence-based warnings
- Clear uncertainty handling

## 📝 Logging & Debugging

Logs are saved to `logs/app.log` and console output.

Set log level in `config/settings.py`:
```python
LOG_LEVEL = "DEBUG"  # or INFO, WARNING, ERROR
```

View evaluation reports:
```bash
cat evaluation/eval_*.json
```

## 🤝 Contributing

Areas for enhancement:
1. Add more sophisticated reasoning models
2. Implement actual LLM integration (GPT-4, etc.)
3. Add multi-language support
4. Extend evaluation metrics
5. Build UI frontend (Streamlit/Chainlit)

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - Detailed system architecture
- [Agent Guide](docs/AGENT_GUIDE.md) - Agent-specific documentation
- [API Reference](docs/API_REFERENCE.md) - API documentation
- [Evaluation Guide](docs/EVALUATION_GUIDE.md) - Evaluation metrics and methods

## 📄 License

[Your License Here]

## 👥 Authors

Created as an enterprise knowledge operations AI system demonstration.

## ❓ FAQ

**Q: How do I add more documents?**
A: Use `agent.ingest_text()` or `agent.ingest_document()` methods.

**Q: Can I customize agent behavior?**
A: Yes, each agent class can be subclassed to override behavior.

**Q: How accurate is the system?**
A: Accuracy depends on document quality and query specificity. See evaluation metrics.

**Q: Can this scale to production?**
A: The current implementation is for learning. Production would require:
- Cloud deployment (AWS, Azure, GCP)
- Larger vector database (Pinecone, Weaviate)
- Production LLM endpoints
- Enhanced security and authentication

## 🚀 Next Steps

1. Run `python main.py --demo` to see the system in action
2. Review `docs/ARCHITECTURE.md` for detailed design
3. Explore agent implementations in `agents/`
4. Check evaluation reports in `evaluation/` directory
5. Customize configuration in `config/settings.py`

---

**Status**: MVP Complete ✅
**Version**: 1.0
**Last Updated**: October 2026
