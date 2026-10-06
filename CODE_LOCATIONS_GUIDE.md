# Document Storage - Code Locations & Visual Guide

## Quick Visual: Document Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  YOUR DOCUMENTS                                         │
├─────────────────────────────────────────────────────────┤
│ • Files on disk (data/documents/*.txt)                  │
│ • In-memory strings (main.py hardcoded)                 │
│ • External sources (API, Database, Cloud)              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  DocumentManager               │
        │  .ingest_document()            │
        │  .ingest_text()                │
        │  (core/document_manager.py)    │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  DocumentProcessor             │
        │  .chunk_document()             │
        │  (core/document_manager.py)    │
        │                                │
        │  Splits into 1000-char chunks  │
        │  with 100-char overlap         │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Embedding Model               │
        │  all-MiniLM-L6-v2              │
        │                                │
        │  Converts text → 384 dims      │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  CHROMA VECTOR DATABASE        │
        │  (data/vector_store/)          │
        │                                │
        │  Stores:                       │
        │  • Embeddings (vectors)        │
        │  • Text content                │
        │  • Metadata (source, title)    │
        └────────────────┬───────────────┘
                         │
        ┌────────────────┴────────────────┐
        │ Persisted on Disk               │
        │ (chroma.sqlite3 + .bin files)   │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  User Question                 │
        │  "What are work hours?"        │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Semantic Search               │
        │  RetrieverAgent.search()       │
        │  agents/retriever_agent.py     │
        │                                │
        │  Finds 5 most similar chunks   │
        │  Returns with relevance scores │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Answer Generation             │
        │  AnalyzerAgent.analyze()       │
        │  agents/analyzer_agent.py      │
        │                                │
        │  Synthesizes into response     │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Verification                  │
        │  VerifierAgent.verify()        │
        │  agents/verifier_agent.py      │
        │                                │
        │  Grounding check: 0.92         │
        │  Confidence: high              │
        └────────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  USER GETS ANSWER              │
        │  With sources, grounding score │
        └────────────────────────────────┘
```

---

## EXACT CODE LOCATIONS

### 1. Where Documents Are Currently Loaded

**File**: `main.py`
**Lines**: 41-140
**Function**: `setup_sample_documents()`

```python
async def setup_sample_documents(agent, doc_manager):
    """Sample documents are defined here"""
    
    # Policy Document (lines 47-75)
    policy_doc = """COMPANY DATA PROTECTION POLICY..."""
    agent.ingest_text(policy_doc, "Data Protection Policy")
    
    # Onboarding SOP (lines 78-103)
    sop_doc = """STANDARD OPERATING PROCEDURE..."""
    agent.ingest_text(sop_doc, "Onboarding SOP")
    
    # IT Security (lines 106-120)
    security_doc = """IT SECURITY STANDARDS..."""
    agent.ingest_text(security_doc, "IT Security")
    
    # Benefits (lines 123-138)
    benefits_doc = """BENEFITS & COMPENSATION..."""
    agent.ingest_text(benefits_doc, "Benefits")
```

**To see ALL sample documents**: Open `main.py` and scroll to line 41

---

### 2. Document Ingestion Code

**File**: `core/document_manager.py`
**Class**: `DocumentManager` (lines 166+)

```python
class DocumentManager:
    def __init__(self):
        self.processor = DocumentProcessor()
        self.vector_db = VectorDatabase()
        self.documents = {}
    
    # Method 1: Ingest from file
    def ingest_document(self, file_path: str) -> Document:
        # LINE 176-220
        # Reads file, creates Document, processes chunks
        pass
    
    # Method 2: Ingest from text
    def ingest_text(self, text: str, title: str):
        # LINE 222-240
        # Creates Document from string
        pass
    
    # Search
    def search(self, query: str) -> List:
        # LINE 242-260
        # Delegates to vector_db.search()
        pass
```

---

### 3. Text Chunking Logic

**File**: `core/document_manager.py`
**Class**: `DocumentProcessor`
**Lines**: 24-66
**Function**: `chunk_document()`

```python
@staticmethod
def chunk_document(document: Document, 
                  chunk_size: int = 1000,  # Characters
                  overlap: int = 100):     # Overlap chars
    """
    LINE 24-66: How documents are chunked
    
    Example:
    Input: "Long document with 5000 characters"
    
    Output chunks:
    - Chunk 0: chars 0-1000
    - Chunk 1: chars 900-1900 (overlap!)
    - Chunk 2: chars 1800-2800
    - ...
    """
    pass
```

**Key code**:
```python
while start < len(content):
    end = min(start + chunk_size, len(content))
    chunk_text = content[start:end]
    
    # Create chunk with metadata
    chunk = DocumentChunk(
        id=f"{document.id}_chunk_{chunk_index}",
        document_id=document.id,
        content=chunk_text,
        chunk_index=chunk_index,
        metadata={
            "source": document.source_path,
            "title": document.title,
            "document_created": document.created_at.isoformat()
        }
    )
    
    # Move to next chunk with overlap
    start = end - overlap
    chunk_index += 1
```

---

### 4. Vector Database Storage

**File**: `core/document_manager.py`
**Class**: `VectorDatabase`
**Lines**: 69-164

```python
class VectorDatabase:
    def __init__(self, persist_path: str = "data/vector_store"):
        # LINE 78-80
        # Creates Chroma client with persistence
        self.client = chromadb.PersistentClient(path=persist_path)
    
    def get_or_create_collection(self):
        # LINE 90-97
        # Creates "enterprise_docs" collection
        self.collection = self.client.get_or_create_collection(
            name="enterprise_docs",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, chunks):
        # LINE 105-120
        # Stores chunks in Chroma
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,      # 384-dim vectors
            documents=chunk_texts,      # Original text
            metadatas=metadata          # Source info
        )
    
    def search(self, query: str, n_results: int = 5):
        # LINE 126-147
        # Performs semantic search
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return formatted_results
```

**Physical Storage Location**:
```
C:\repos\ai-engineering-lead\data\vector_store\
├── chroma.sqlite3              ← Index & metadata
├── 1efdfe5f-3b41.../
│   ├── data_level0.bin         ← Embeddings (binary)
│   ├── header.bin              ← Headers
│   ├── length.bin              ← Chunk lengths
│   └── link_lists.bin          ← Search index (HNSW)
```

---

### 5. Retrieval During Q&A

**File**: `agents/retriever_agent.py`
**Lines**: 50-120
**Function**: `process()`

```python
async def process(self, input_data):
    # LINE 50-120
    # 1. Gets query from input_data
    query = input_data.get('query')
    
    # 2. Calls vector_db.search()
    results = self.doc_manager.search(query, n_results=5)
    
    # 3. Scores relevance
    for result in results:
        result['relevance_score'] = calculate_relevance(...)
    
    # 4. Returns RetrievalResult objects
    retrieval_results = [
        RetrievalResult(
            chunk_id=r['id'],
            content=r['content'],
            source=r['metadata']['source'],
            relevance_score=r['relevance_score']
        )
        for r in results
    ]
    return retrieval_results
```

---

### 6. Answer Synthesis from Retrieved Documents

**File**: `agents/analyzer_agent.py`
**Lines**: 100-180
**Function**: `_synthesize_answer()`

```python
async def _synthesize_answer(self, query: str, 
                           retrieved_docs: List[RetrievalResult]):
    # LINE 100-180
    # Takes retrieved chunks and creates answer
    
    # Step 1: Group by source
    by_source = {}
    for doc in retrieved_docs:
        if doc.source not in by_source:
            by_source[doc.source] = []
        by_source[doc.source].append(doc)
    
    # Step 2: Generate synthesis
    answer = f"Based on {len(retrieved_docs)} source(s):\n"
    
    for source, docs in by_source.items():
        answer += f"\n1. From {source}:\n"
        for doc in docs:
            answer += f"   {doc.content}\n"
    
    return answer
```

---

### 7. Verification of Grounding

**File**: `agents/verifier_agent.py`
**Lines**: 100-123
**Function**: `_verify_grounding()`

```python
async def _verify_grounding(self, answer: str, 
                           documents: List[RetrievalResult]):
    # LINE 100-123
    # Checks if answer is supported by retrieved documents
    
    # Calculate average relevance
    avg_relevance = sum(d.relevance_score for d in documents) / len(documents)
    
    # If avg relevance >= 0.5, answer is grounded
    if avg_relevance >= 0.5:
        grounding_score = min(0.8 + (avg_relevance * 0.2), 1.0)
    else:
        grounding_score = avg_relevance
    
    return grounding_score  # Returns 0-1
```

---

## WHERE EACH QUESTION GETS ANSWERS FROM

### Question: "What are the work hour policies?"

```
1. Question received by Orchestrator
   ↓
2. Retriever queries: "work hour policies?"
   ↓
3. Chroma semantic search finds most similar chunks:
   ✓ "Work hours are 9am-5pm..." (relevance: 0.92)
   ✓ "Remote work available 2 days..." (relevance: 0.85)
   ✓ "Must be in office Mon-Fri..." (relevance: 0.78)
   
   (These came from: data/vector_store/ → originally from main.py)
   ↓
4. Analyzer synthesizes:
   "Based on Employee Handbook:
    - Work hours are 9am-5pm
    - Remote work available 2 days per week
    ..."
   ↓
5. Verifier confirms:
   - Grounding Score: 0.92 (excellent!)
   - Confidence: high
   - All statements backed by documents
   ↓
6. User sees answer with sources
```

---

## HOW TO USE YOUR OWN DOCUMENTS

### Scenario 1: Add a Text File
```powershell
# 1. Create file
"C:\repos\ai-engineering-lead\data\documents\my_policy.txt"

# 2. Modify main.py
doc = doc_manager.ingest_document("data/documents/my_policy.txt")
await setup_sample_documents(agent, doc_manager)

# 3. Run
python main.py

# 4. Ask questions - Chroma will search your document!
"What does my policy say?"
```

### Scenario 2: Load Multiple Files Automatically
```python
# In main.py, modify setup_sample_documents():

from pathlib import Path

docs_dir = Path("data/documents")
for doc_file in docs_dir.glob("*.txt"):
    doc = doc_manager.ingest_document(str(doc_file))
    logger.info(f"Loaded: {doc.title}")

# All documents now in Chroma, searchable!
```

### Scenario 3: Load from External API
```python
# In main.py:

import requests

# Fetch documents from your API
response = requests.get("https://api.company.com/policies")
policies = response.json()

for policy in policies:
    agent.ingest_text(policy['content'], policy['title'])

# Questions now search your API documents!
```

---

## WHAT HAPPENS INSIDE CHROMA

When you ask "What are the work hour policies?":

```python
# 1. Question → Vector
query = "What are the work hour policies?"
query_vector = [0.123, -0.456, 0.789, ...]  # 384 dimensions

# 2. Chroma finds closest vectors in database
# Using HNSW algorithm (fast approximate search)

# 3. Returns top 5 chunks:
[
    {
        "id": "doc_2_chunk_3",
        "content": "Work hours are 9am-5pm...",
        "metadata": {"source": "Employee Handbook", "title": "Work Hours"},
        "distance": 0.15  # Closer to query = better match
    },
    {
        "id": "doc_2_chunk_4",
        "content": "Remote work available 2 days per week...",
        "metadata": {"source": "Employee Handbook"},
        "distance": 0.22
    },
    ...
]

# 4. These chunks used to generate answer
```

---

## Storage Summary

| Component | Location | Type | Persists? |
|-----------|----------|------|-----------|
| Sample documents | main.py (lines 47-138) | Hardcoded | During runtime |
| Document files | data/documents/ | Disk files | Yes |
| Vector DB index | data/vector_store/chroma.sqlite3 | SQLite DB | Yes |
| Embeddings | data/vector_store/.../*.bin | Binary files | Yes |
| Chunk metadata | data/vector_store/chroma.sqlite3 | SQLite DB | Yes |
| Original text | Chroma collection | In memory | After ingest |

**Key Point**: Documents are stored in Chroma's persistent database, which survives restarts!

---

## Debug: See What's in Chroma

```python
# Add this to any Python script:

from core.document_manager import VectorDatabase

vdb = VectorDatabase()
collection = vdb.client.get_collection("enterprise_docs")

# Get all data
all_data = collection.get()

print(f"Total chunks: {len(all_data['ids'])}")
print(f"\nChunk IDs: {all_data['ids']}")
print(f"\nChunk contents (first 200 chars):")
for doc in all_data['documents']:
    print(f"  {doc[:200]}...")

print(f"\nMetadata:")
for meta in all_data['metadatas']:
    print(f"  Source: {meta.get('source')}, Title: {meta.get('title')}")
```

---

## Summary: Your Question → Answer

```
USER QUESTION
     ↓
Chroma Semantic Search
(finds similar chunks from vector_store/)
     ↓
Retrieved Chunks (with source document name)
     ↓
Answer Generation
(synthesizes retrieved text)
     ↓
Answer Verification
(checks grounding)
     ↓
USER GETS ANSWER
with sources cited and grounding score
```

**All documents come from Chroma vector database!**
