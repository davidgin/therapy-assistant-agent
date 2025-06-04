"""
FAISS Vector Database Service for RAG (Retrieval-Augmented Generation)
Handles clinical knowledge base embeddings and similarity search
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import faiss
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VectorDatabaseService:
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        index_path: str = "data/vector_db/clinical_knowledge.faiss",
        metadata_path: str = "data/vector_db/clinical_knowledge_metadata.json"
    ):
        """
        Initialize FAISS vector database service
        
        Args:
            model_name: SentenceTransformer model for embeddings
            index_path: Path to save/load FAISS index
            metadata_path: Path to save/load document metadata
        """
        self.model_name = model_name
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = None
        self.document_metadata = []
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # Load existing index if available
        self.load_index()
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts
        
        Args:
            texts: List of text documents to embed
            
        Returns:
            numpy array of embeddings
        """
        logger.info(f"Creating embeddings for {len(texts)} documents")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings.astype(np.float32)
    
    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Build FAISS index from clinical documents
        
        Args:
            documents: List of documents with 'text' and metadata fields
        """
        logger.info(f"Building FAISS index with {len(documents)} documents")
        
        # Extract texts for embedding
        texts = [doc['text'] for doc in documents]
        
        # Create embeddings
        embeddings = self.create_embeddings(texts)
        
        # Create FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        # Store metadata
        self.document_metadata = documents
        
        logger.info(f"FAISS index built with {self.index.ntotal} documents")
        
        # Save index and metadata
        self.save_index()
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add new documents to existing index
        
        Args:
            documents: List of documents to add
        """
        if not documents:
            return
            
        logger.info(f"Adding {len(documents)} documents to existing index")
        
        # Create index if it doesn't exist
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Extract texts and create embeddings
        texts = [doc['text'] for doc in documents]
        embeddings = self.create_embeddings(texts)
        
        # Normalize embeddings
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Add metadata
        self.document_metadata.extend(documents)
        
        logger.info(f"Added documents. Total documents: {self.index.ntotal}")
        
        # Save updated index
        self.save_index()
    
    def search(
        self, 
        query: str, 
        k: int = 5, 
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the knowledge base
        
        Args:
            query: Search query text
            k: Number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of similar documents with scores and metadata
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("No documents in vector database")
            return []
        
        logger.info(f"Searching for: '{query[:50]}...' (k={k})")
        
        # Create query embedding
        query_embedding = self.embedding_model.encode([query]).astype(np.float32)
        faiss.normalize_L2(query_embedding)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding, k)
        
        # Format results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if score >= score_threshold:
                result = {
                    "rank": i + 1,
                    "score": float(score),
                    "document_id": idx,
                    "metadata": self.document_metadata[idx] if idx < len(self.document_metadata) else {},
                    "text": self.document_metadata[idx].get('text', '') if idx < len(self.document_metadata) else ''
                }
                results.append(result)
        
        logger.info(f"Found {len(results)} relevant documents")
        return results
    
    def search_by_disorder(
        self, 
        query: str, 
        disorder: str, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for documents specific to a disorder
        
        Args:
            query: Search query
            disorder: Disorder name to filter by
            k: Number of results
            
        Returns:
            Filtered search results
        """
        # Get all results first
        all_results = self.search(query, k * 2)  # Get more to filter
        
        # Filter by disorder
        disorder_results = []
        for result in all_results:
            metadata = result.get('metadata', {})
            if disorder.lower() in metadata.get('disorder', '').lower():
                disorder_results.append(result)
                if len(disorder_results) >= k:
                    break
        
        return disorder_results
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get document by its ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document metadata and text
        """
        if 0 <= doc_id < len(self.document_metadata):
            return self.document_metadata[doc_id]
        return None
    
    def save_index(self) -> None:
        """Save FAISS index and metadata to disk"""
        if self.index is not None:
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            logger.info(f"FAISS index saved to {self.index_path}")
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.document_metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadata saved to {self.metadata_path}")
    
    def load_index(self) -> bool:
        """
        Load FAISS index and metadata from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                # Load FAISS index
                self.index = faiss.read_index(self.index_path)
                
                # Load metadata
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.document_metadata = json.load(f)
                
                logger.info(f"Loaded FAISS index with {self.index.ntotal} documents")
                return True
                
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
            
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        stats = {
            "total_documents": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.embedding_dim,
            "model_name": self.model_name,
            "index_exists": self.index is not None
        }
        
        if self.document_metadata:
            # Analyze document types
            doc_types = {}
            disorders = set()
            for doc in self.document_metadata:
                doc_type = doc.get('type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
                if 'disorder' in doc:
                    disorders.add(doc['disorder'])
            
            stats['document_types'] = doc_types
            stats['disorders_covered'] = len(disorders)
            stats['disorder_list'] = sorted(list(disorders))
        
        return stats

# Global instance
vector_db = VectorDatabaseService()

def get_vector_db() -> VectorDatabaseService:
    """Get the global vector database instance"""
    return vector_db