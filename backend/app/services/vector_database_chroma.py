"""
ChromaDB Vector Database Service for RAG (Retrieval-Augmented Generation)
Lightweight in-process alternative to FAISS
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ChromaVectorDatabaseService:
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        persist_directory: str = "data/chroma_db"
    ):
        """
        Initialize ChromaDB vector database service
        
        Args:
            model_name: SentenceTransformer model for embeddings
            persist_directory: Directory to persist ChromaDB data
        """
        self.model_name = model_name
        self.persist_directory = persist_directory
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection_name = "clinical_knowledge"
        try:
            self.collection = self.client.get_collection(self.collection_name)
            logger.info(f"Loaded existing ChromaDB collection: {self.collection_name}")
        except:
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Clinical knowledge base for therapy assistant"}
            )
            logger.info(f"Created new ChromaDB collection: {self.collection_name}")
        
        # Initialize embedding model (ChromaDB can handle this automatically)
        self.embedding_model = None
        try:
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}. Using ChromaDB default.")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector database
        
        Args:
            documents: List of documents with 'text' and metadata fields
        """
        if not documents:
            return
            
        logger.info(f"Adding {len(documents)} documents to ChromaDB")
        
        # Prepare data for ChromaDB
        texts = [doc['text'] for doc in documents]
        ids = [f"doc_{i}" for i in range(len(documents))]
        metadatas = []
        
        for i, doc in enumerate(documents):
            metadata = doc.copy()
            metadata.pop('text', None)  # Remove text from metadata
            metadata['doc_id'] = i
            metadatas.append(metadata)
        
        # Generate embeddings if we have the model
        embeddings = None
        if self.embedding_model:
            try:
                embeddings = self.embedding_model.encode(texts).tolist()
            except Exception as e:
                logger.warning(f"Could not generate embeddings: {e}")
        
        # Add to collection
        if embeddings:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
        else:
            # Let ChromaDB generate embeddings
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
        
        logger.info(f"Added {len(documents)} documents to ChromaDB collection")
    
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
        try:
            # Search in ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0] if results['metadatas'] else [{}] * len(results['documents'][0]),
                    results['distances'][0] if results['distances'] else [0.0] * len(results['documents'][0])
                )):
                    # Convert distance to similarity score (1 - distance for cosine)
                    score = 1.0 - distance
                    
                    if score >= score_threshold:
                        result = {
                            "rank": i + 1,
                            "score": float(score),
                            "document_id": metadata.get('doc_id', i),
                            "metadata": metadata,
                            "text": doc
                        }
                        formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} relevant documents for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return []
    
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
        try:
            # Search with metadata filtering
            results = self.collection.query(
                query_texts=[query],
                n_results=k * 2,  # Get more to filter
                where={"disorder": {"$contains": disorder.lower()}}
            )
            
            # Format results (same as regular search)
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0] if results['metadatas'] else [{}] * len(results['documents'][0]),
                    results['distances'][0] if results['distances'] else [0.0] * len(results['documents'][0])
                )):
                    score = 1.0 - distance
                    result = {
                        "rank": i + 1,
                        "score": float(score),
                        "document_id": metadata.get('doc_id', i),
                        "metadata": metadata,
                        "text": doc
                    }
                    formatted_results.append(result)
                    
                    if len(formatted_results) >= k:
                        break
            
            return formatted_results
            
        except Exception as e:
            logger.warning(f"Filtered search failed, falling back to regular search: {e}")
            # Fallback to regular search and filter manually
            all_results = self.search(query, k * 2)
            return [r for r in all_results if disorder.lower() in r.get('metadata', {}).get('disorder', '').lower()][:k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            count = self.collection.count()
            stats = {
                "total_documents": count,
                "collection_name": self.collection_name,
                "model_name": self.model_name,
                "persist_directory": self.persist_directory,
                "database_type": "ChromaDB"
            }
            
            # Try to get some sample metadata to analyze document types
            if count > 0:
                sample_results = self.collection.get(limit=min(count, 100))
                if sample_results['metadatas']:
                    doc_types = {}
                    disorders = set()
                    for metadata in sample_results['metadatas']:
                        if isinstance(metadata, dict):
                            doc_type = metadata.get('type', 'unknown')
                            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                            
                            disorder = metadata.get('disorder')
                            if disorder:
                                disorders.add(disorder)
                    
                    stats['document_types'] = doc_types
                    stats['disorders_covered'] = len(disorders)
                    stats['disorder_list'] = sorted(list(disorders))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting ChromaDB stats: {e}")
            return {
                "total_documents": 0,
                "error": str(e),
                "database_type": "ChromaDB"
            }
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Clinical knowledge base for therapy assistant"}
            )
            logger.info("Cleared ChromaDB collection")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")

# Global instance
chroma_db = ChromaVectorDatabaseService()

def get_chroma_db() -> ChromaVectorDatabaseService:
    """Get the global ChromaDB instance"""
    return chroma_db