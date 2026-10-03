"""Document ingestion and vector database management."""

import os
import logging
from typing import List
import hashlib
from pathlib import Path

import chromadb

from config.settings import (
    CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_DB_PERSIST_PATH,
    DEFAULT_EMBEDDING_MODEL, DOCUMENTS_DIR
)
from core.types import Document, DocumentChunk

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document chunking and preparation."""
    
    @staticmethod
    def chunk_document(document: Document, chunk_size: int = CHUNK_SIZE, 
                      overlap: int = CHUNK_OVERLAP) -> List[DocumentChunk]:
        """
        Split a document into chunks with overlap.
        
        Args:
            document: Document to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        content = document.content
        chunk_index = 0
        start = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk_text = content[start:end]
            
            chunk_id = f"{document.id}_chunk_{chunk_index}"
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=document.id,
                content=chunk_text,
                chunk_index=chunk_index,
                metadata={
                    "source": document.source_path,
                    "title": document.title,
                    "document_created": document.created_at.isoformat()
                }
            )
            chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = end - overlap if end < len(content) else end
            chunk_index += 1
            
        document.chunks = chunks
        logger.info(f"Chunked document '{document.title}' into {len(chunks)} chunks")
        return chunks


class VectorDatabase:
    """Manages interactions with the Chroma vector database."""
    
    def __init__(self, persist_path: str = VECTOR_DB_PERSIST_PATH):
        """Initialize vector database connection."""
        self.persist_path = persist_path
        
        # Initialize Chroma client with persistence (new API)
        try:
            self.client = chromadb.PersistentClient(path=persist_path)
            logger.info(f"Initialized Chroma PersistentClient with path: {persist_path}")
        except Exception as e:
            logger.warning(f"Could not initialize PersistentClient: {e}. Trying EphemeralClient.")
            self.client = chromadb.EphemeralClient()
        
        self.collection = None
        
    def get_or_create_collection(self, collection_name: str = "enterprise_docs"):
        """Get or create a collection."""
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Collection '{collection_name}' ready")
        return self.collection
    
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to the vector database.
        
        Args:
            chunks: List of DocumentChunk objects to add
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(chunks)} chunks to vector database")
    
    def search(self, query: str, n_results: int = 5) -> List[dict]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Reformat results
        formatted_results = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'id': results['ids'][0][i] if results['ids'] else None,
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        logger.info(f"Search for '{query}' returned {len(formatted_results)} results")
        return formatted_results
    
    def delete_collection(self, collection_name: str = "enterprise_docs"):
        """Delete a collection."""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
    
    def persist(self):
        """Persist the vector database to disk."""
        try:
            self.client.persist()
            logger.info("Vector database persisted to disk")
        except Exception as e:
            logger.warning(f"Could not persist database: {e}")


class DocumentManager:
    """Manages document lifecycle - ingestion, chunking, and storage."""
    
    def __init__(self):
        """Initialize document manager."""
        self.processor = DocumentProcessor()
        self.vector_db = VectorDatabase()
        self.vector_db.get_or_create_collection()
        self.documents: dict = {}
    
    def ingest_document(self, file_path: str, document_id: str = None) -> Document:
        """
        Ingest a document from file.
        
        Args:
            file_path: Path to the document file
            document_id: Optional custom ID for the document
            
        Returns:
            Processed Document object
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate document ID if not provided
        if document_id is None:
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            document_id = f"{file_path.stem}_{content_hash}"
        
        # Create document object
        document = Document(
            id=document_id,
            title=file_path.stem,
            content=content,
            source_path=str(file_path)
        )
        
        # Process and store
        chunks = self.processor.chunk_document(document)
        self.vector_db.add_documents(chunks)
        self.documents[document_id] = document
        
        logger.info(f"Ingested document: {document.title} ({len(chunks)} chunks)")
        return document
    
    def ingest_text(self, text: str, title: str, document_id: str = None) -> Document:
        """
        Ingest document from raw text.
        
        Args:
            text: Document content as string
            title: Document title
            document_id: Optional custom ID
            
        Returns:
            Processed Document object
        """
        if document_id is None:
            content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            document_id = f"{title}_{content_hash}"
        
        document = Document(
            id=document_id,
            title=title,
            content=text,
            source_path=f"in_memory://{title}"
        )
        
        chunks = self.processor.chunk_document(document)
        self.vector_db.add_documents(chunks)
        self.documents[document_id] = document
        
        logger.info(f"Ingested text document: {title} ({len(chunks)} chunks)")
        return document
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant document chunks
        """
        results = self.vector_db.search(query, n_results=top_k)
        
        # Convert distances to similarity scores (0-1 range)
        for result in results:
            if result.get('distance') is not None:
                # Convert cosine distance to similarity (1 - distance)
                result['relevance_score'] = 1 - result['distance']
            else:
                result['relevance_score'] = 0.5
        
        return results
    
    def persist(self):
        """Persist all data to disk."""
        self.vector_db.persist()
