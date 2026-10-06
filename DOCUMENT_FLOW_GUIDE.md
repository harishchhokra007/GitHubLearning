# Document Storage & Retrieval - Complete Guide

## Quick Answer

**Yes, documents ARE stored in Chroma (vector database) only**, but here's the complete flow:

```
Your Document File (PDF/TXT)
        ↓
   Document Ingestion
        ↓
   Text Chunking (overlap)
        ↓
   Embedding Generation (ONNX model)
        ↓
   Chroma Vector Database Storage
        ↓
   Semantic Search for Questions
        ↓
   Retrieved Chunks → Answer Generation
```

---

## 1. WHERE DOCUMENTS COME FROM

### Option A: Sample Documents (Currently Used)
**Location**: Hardcoded in `main.py` (lines 41-140)

These are loaded in memory and then ingested:
```python
# From main.py
policy_doc = """COMPANY DATA PROTECTION POLICY
...content...
"""

agent.ingest_text(policy_doc, "Data Protection Policy")
```

**Current Sample Documents**:
1. `Data Protection Policy` - Company data handling guidelines
2. `Employee Onboarding SOP` - New hire procedures
3. `IT Security Standards` - Security requirements
4. `Benefits & Compensation` - Employee benefits
5. `Code of Conduct` - Professional conduct guidelines

### Option B: Document Files from Disk
**Location**: `data/documents/` (recommended for production)

You can place files here:
```
C:\repos\ai-engineering-lead\data\documents\
├── policy.txt
├── employee_handbook.docx
├── security_standards.pdf
└── procedures.md
```

Then load them in code:
```python
# From core/document_manager.py
doc = doc_manager.ingest_document("data/documents/policy.txt")
```

---

## 2. DOCUMENT FLOW DIAGRAM

### Step 1: Document Ingestion
```python
# core/document_manager.py - Lines 176-220
def ingest_document(self, file_path: str) -> Document:
    # Reads file from disk
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Creates Document object
    document = Document(
        id=document_id,
        title=file_path.stem,
        content=content,
        source_path=file_path
    )
    
    return document
```

**Result**: Content in memory as `Document` object

---

### Step 2: Document Chunking
```python
# core/document_manager.py - Lines 24-66
# DocumentProcessor.chunk_document()

document_content = "Long text..."  # Could be 10,000+ characters
chunk_size = 1000  # Characters per chunk
overlap = 100      # Characters to repeat between chunks

# Creates chunks like:
Chunk 1: chars 0-1000
Chunk 2: chars 900-1900  (overlap!)
Chunk 3: chars 1800-2800
...
```

**Why chunking?**
- Vector databases work better with smaller text pieces
- Overlap preserves context between chunks
- Semantic search finds relevant chunks faster

**Result**: Document split into `DocumentChunk` objects with metadata

---

### Step 3: Embedding Generation
```python
# core/document_manager.py - Lines 119-128
# VectorDatabase.add_documents()

embeddings = []
for chunk in document_chunks:
    # ONNX model (all-MiniLM-L6-v2) generates 384-dimensional vector
    embedding = model.encode(chunk.content)
    embeddings.append(embedding)

# Stored in Chroma
```

**Model Used**: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- Automatically downloaded on first run
- Stored in: `C:\Users\chhokha\.cache\chroma\onnx_models\`
- Fast inference (~50ms per document)

**Result**: Each chunk becomes a vector (384 numbers)

---

### Step 4: Storage in Chroma Vector Database
```python
# core/document_manager.py - Lines 105-120
# VectorDatabase.add_documents()

self.collection.add(
    ids=chunk_ids,
    embeddings=embeddings,  # 384-dim vectors
    documents=chunk_texts,  # Original text
    metadatas=metadata      # Source, title, etc.
)
```

**Storage Location**: `data/vector_store/` (persistent disk storage)

```
C:\repos\ai-engineering-lead\data\vector_store\
├── chroma.sqlite3                    # Index database
└── 1efdfe5f-3b41-4927-9472-56f1397d4f5e/
    ├── data_level0.bin              # Vector data (binary)
    ├── header.bin                   # Metadata headers
    ├── length.bin                   # Length information
    └── link_lists.bin               # Search index structures
```

**What Chroma stores**:
- ✓ Vectors (embeddings) - for semantic search
- ✓ Text content - for display
- ✓ Metadata - source, title, chunk_id, etc.
- ✓ Index structures - for fast lookup (HNSW algorithm)

**Result**: Data persisted in vector database

---

### Step 5: Semantic Search for Queries
```python
# core/document_manager.py - Lines 126-147
# VectorDatabase.search()

def search(self, query: str, n_results: int = 5):
    # User asks: "What are the work hour policies?"
    
    # Convert question to embedding (same model)
    query_embedding = encoder.encode(query)  # 384-dim vector
    
    # Find similar chunks in Chroma
    results = self.collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results  # Top 5 most similar
    )
    
    # Returns:
    # - Chunk IDs
    # - Chunk content (original text)
    # - Relevance scores (0-1)
    # - Metadata (source document)
```

**How it finds answers**:
1. Question → Vector (384 numbers)
2. Find K nearest vectors to question vector
3. Return the closest chunk texts
4. Score by distance (closer = more relevant)

**Result**: Retrieved documents with relevance scores

---

### Step 6: Response Generation
```python
# agents/analyzer_agent.py - Lines 100-180
# Analyzer synthesizes retrieved chunks into answer

retrieved_chunks = [
    {
        "content": "Work hours are 9am-5pm...",
        "source": "Employee Handbook",
        "relevance": 0.92
    },
    {
        "content": "Remote work available 2 days per week...",
        "source": "Employee Handbook",
        "relevance": 0.85
    }
]

# Template-based synthesis
answer = f"""
Based on {len(retrieved_chunks)} document(s):
1. From {source}: {content}
2. From {source}: {content}
...
"""
```

**Result**: Answer with sources cited

---

## 3. DATA STRUCTURES

### Document Object
```python
# From core/types.py
@dataclass
class Document:
    id: str                  # Unique identifier
    title: str              # Document title
    content: str            # Full text content
    source_path: str        # File path or "in_memory"
    created_at: datetime    # When loaded
    chunks: List[DocumentChunk] = None
    metadata: Dict = None
```

### DocumentChunk Object
```python
@dataclass
class DocumentChunk:
    id: str                 # e.g., "doc_1_chunk_0"
    document_id: str        # Reference to parent document
    content: str            # Chunk text (1000 chars)
    chunk_index: int        # Position in document
    embedding: List[float] = None  # 384-dim vector
    metadata: Dict = None
    
    # Metadata contains:
    # - source: "Employee Handbook"
    # - title: "Work Hours Policy"
    # - document_created: ISO timestamp
```

### RetrievalResult (What's returned from search)
```python
@dataclass
class RetrievalResult:
    chunk_id: str           # Which chunk
    content: str            # Chunk text
    document_id: str        # Which document
    source: str             # Document name
    relevance_score: float  # 0-1 (how similar to question)
    metadata: Dict
```

---

## 4. HOW TO USE YOUR OWN DOCUMENTS

### Method 1: Add Text Files to data/documents/
```powershell
# Step 1: Create text files
"C:\repos\ai-engineering-lead\data\documents\my_policy.txt"

# Step 2: Load in code
doc_manager = DocumentManager()
doc = doc_manager.ingest_document("data/documents/my_policy.txt")

# Step 3: Run queries - they'll now use your document
```

### Method 2: Load Documents Programmatically
```python
# core/orchestration.py - EnterpriseKnowledgeAgent class

async def ingest_text(self, text: str, title: str) -> None:
    """Ingest text directly (no file needed)"""
    document = Document(
        id=f"doc_{uuid4()}",
        title=title,
        content=text,
        source_path="in_memory"
    )
    # Store in vector DB
    chunks = self.doc_manager.processor.chunk_document(document)
    self.doc_manager.vector_db.add_documents(chunks)
```

### Method 3: Update main.py
```python
# main.py - setup_sample_documents() function

# Add your documents here:
your_document = """
YOUR POLICY CONTENT HERE
...
"""

agent.ingest_text(your_document, "My Document Title")
```

---

## 5. WHERE TO FIND CODE

| Purpose | File | Lines |
|---------|------|-------|
| Document ingestion | core/document_manager.py | 176-220 |
| Text chunking | core/document_manager.py | 24-66 |
| Vector storage | core/document_manager.py | 69-164 |
| Semantic search | core/document_manager.py | 126-147 |
| Question processing | agents/retriever_agent.py | 50-120 |
| Answer generation | agents/analyzer_agent.py | 100-180 |
| Sample docs | main.py | 41-140 |

---

## 6. CHROMA VECTOR DATABASE DETAILS

### What's Stored
```
Collection: "enterprise_docs"

id: "doc_1_chunk_0"
embedding: [0.123, -0.456, 0.789, ...]  # 384 dimensions
document: "Work hours are 9am-5pm..."    # Original text
metadata: {
    "source": "Employee Handbook",
    "title": "Work Hours",
    "document_created": "2026-10-03"
}
```

### Search Process (Approximate Nearest Neighbor)
```
1. Query: "work hours?"
2. Embed: [0.111, -0.222, 0.333, ...]  # 384 dims
3. Find 5 chunks closest to query vector
4. Return: Top 5 with distances/relevance scores
```

### Persistence
```
C:\repos\ai-engineering-lead\data\vector_store\

- Stored on disk: YES (PersistentClient)
- Survives restarts: YES
- Scalable: YES (but unoptimized for 1M+ documents)
- Real-time updates: YES
```

---

## 7. CURRENT DOCUMENT SOURCES

### Sample Documents in main.py:
```
1. Data Protection Policy
   - Topics: Classification, encryption, incident response
   - Size: ~500 words
   
2. Employee Onboarding SOP
   - Topics: First 30 days, training, documentation
   - Size: ~400 words
   
3. IT Security Standards
   - Topics: Passwords, 2FA, breach reporting
   - Size: ~300 words
   
4. Benefits & Compensation
   - Topics: Salary bands, benefits, 401k
   - Size: ~400 words
   
5. Code of Conduct
   - Topics: Professional conduct, ethics, harassment
   - Size: ~350 words
```

Total: ~2,000 words of content
Chunks: ~50-70 chunks (with overlap)
Vectors: ~50-70 384-dimensional embeddings

---

## 8. QUICK REFERENCE

### To see what's in Chroma:
```python
# core/document_manager.py - VectorDatabase class
# Uncomment to print all documents:

collection = self.client.get_collection("enterprise_docs")
all_data = collection.get()
for id, doc_text in zip(all_data['ids'], all_data['documents']):
    print(f"{id}: {doc_text[:100]}...")
```

### To list all documents:
```python
# From main.py or any agent
agent.doc_manager.documents.keys()  # Document IDs
```

### To check vector DB size:
```python
# From main.py
collection = agent.doc_manager.vector_db.collection
print(f"Total chunks: {collection.count()}")
```

### To clear and reload:
```python
# Reset vector database
doc_manager.vector_db.delete_collection()
doc_manager.vector_db.get_or_create_collection()

# Then ingest new documents
```

---

## 9. PRODUCTION RECOMMENDATIONS

### For Your Own Documents:

**Option A: Use data/documents/ directory**
```powershell
# 1. Place .txt or .md files in data/documents/
# 2. Modify main.py:
for doc_file in Path("data/documents").glob("*.txt"):
    doc = doc_manager.ingest_document(str(doc_file))
```

**Option B: Load from database**
```python
# Query your database/CMS
documents = fetch_from_db()
for doc in documents:
    agent.ingest_text(doc['content'], doc['title'])
```

**Option C: Load from cloud storage**
```python
# Load from S3, Google Drive, etc.
from s3 import download_document
doc_content = download_document("s3://bucket/policy.txt")
agent.ingest_text(doc_content, "Policy from S3")
```

---

## Summary

| Aspect | Details |
|--------|---------|
| **Documents stored in** | Chroma vector database (persistent) |
| **File location** | `data/vector_store/` on disk |
| **Source documents** | Can be files, in-memory, or API calls |
| **Current sources** | Hardcoded samples in `main.py` |
| **Encoding** | ONNX all-MiniLM-L6-v2 (384-dim) |
| **Search method** | Semantic similarity (vector distance) |
| **Retrievable** | Yes - chunk content + metadata |
| **Modifiable** | Yes - add/update/delete documents |
| **Persistent** | Yes - survives program restarts |

---

## How Questions Get Answered

```
User Question: "What are the work hour policies?"
         ↓
Embedding: [0.123, -0.456, ...]  (384 dims)
         ↓
Chroma Search: Find 5 most similar chunks
         ↓
Retrieved Chunk: "Work hours are 9am-5pm..."
         ↓
Analyzer Agent: Synthesizes into answer
         ↓
Verifier Agent: Validates grounding
         ↓
Response: "Based on Employee Handbook: Work hours are 9am-5pm..."
```

**All documents come from Chroma, which was populated from your sources!**
