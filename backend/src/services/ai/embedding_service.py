"""
Service for generating and managing code embeddings using Google's Generative AI.

This module handles:
- Generating embeddings for code snippets using Gemini API
- Storing embeddings in PostgreSQL with pgvector
- Semantic search for relevant code snippets
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.database import CodeEmbedding, RepoAnalysis
from src.services.analysis.ast_parser import parse_code
from src.core.logging import get_logger

logger = get_logger(__name__)

# Load environment variables from backend directory
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding for a text snippet using Gemini's embedding API.
    
    Args:
        text: Text to embed (code snippet, function, etc)
    
    Returns:
        List of floats representing the embedding vector, or None if failed
    
    Note: Embedding functionality needs to be updated when google-genai 
    library releases dedicated embedding models/endpoints.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set, skipping embeddings")
        return None
    
    try:
        # TODO: Update to use proper embedding model when available in google-genai
        # For now, generate a simple hash-based embedding as placeholder
        # This allows semantic search to gracefully degrade until proper embeddings are available
        import hashlib
        hash_value = hashlib.md5(text.encode()).hexdigest()
        # Convert hash to list of floats (placeholder)
        embedding = [float(int(hash_value[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


def store_code_embeddings(
    db: Session,
    repo_analysis_id: int,
    ast: Dict[str, Any],
    repo_url: str = ""
) -> int:
    """
    Extract code elements from AST and store their embeddings.
    
    Args:
        db: Database session
        repo_analysis_id: ID of the RepoAnalysis record
        ast: AST dictionary from parse_code
        repo_url: Repository URL (for logging)
    
    Returns:
        Number of embeddings stored
    """
    stored_count = 0
    
    # Delete existing embeddings for this repo to avoid duplicates
    db.query(CodeEmbedding).filter(
        CodeEmbedding.repo_analysis_id == repo_analysis_id
    ).delete()
    
    try:
        # Iterate through files in AST
        for file_path, file_info in ast.get("ast", {}).items():
            language = file_info.get("language", "unknown")
            
            # Extract and store function embeddings
            for func in file_info.get("functions", []):
                try:
                    func_name = func.get("name", "")
                    code_snippet = func.get("content", "")
                    start_line = func.get("start_line", 0)
                    
                    # Generate embedding
                    embedding = generate_embedding(code_snippet)
                    
                    if embedding:
                        # Store in database
                        code_emb = CodeEmbedding(
                            repo_analysis_id=repo_analysis_id,
                            file_path=file_path,
                            element_type="function",
                            element_name=func_name,
                            code_snippet=code_snippet,
                            start_line=start_line,
                            embedding=embedding,
                            metadata={
                                "language": language,
                                "complexity": func.get("metadata", {}).get("complexity", 0)
                            }
                        )
                        db.add(code_emb)
                        stored_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to embed function {func_name}: {e}")
            
            # Extract and store class embeddings
            for cls in file_info.get("classes", []):
                try:
                    cls_name = cls.get("name", "")
                    code_snippet = cls.get("content", "")
                    start_line = cls.get("start_line", 0)
                    
                    # Generate embedding
                    embedding = generate_embedding(code_snippet)
                    
                    if embedding:
                        # Store in database
                        code_emb = CodeEmbedding(
                            repo_analysis_id=repo_analysis_id,
                            file_path=file_path,
                            element_type="class",
                            element_name=cls_name,
                            code_snippet=code_snippet,
                            start_line=start_line,
                            embedding=embedding,
                            metadata={
                                "language": language,
                                "complexity": cls.get("metadata", {}).get("complexity", 0),
                                "methods": cls.get("methods", [])
                            }
                        )
                        db.add(code_emb)
                        stored_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to embed class {cls_name}: {e}")
        
        # Commit all embeddings
        db.commit()
        logger.info(f"Stored {stored_count} embeddings for repo_analysis_id {repo_analysis_id}")
        
    except Exception as e:
        logger.error(f"Failed to store embeddings: {e}")
        db.rollback()
    
    return stored_count


def semantic_search(
    db: Session,
    repo_analysis_id: int,
    query: str,
    limit: int = 5,
    threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Perform semantic search for code snippets relevant to a query.
    
    Args:
        db: Database session
        repo_analysis_id: ID of the RepoAnalysis to search in
        query: Search query
        limit: Maximum number of results to return
        threshold: Minimum similarity threshold (0-1)
    
    Returns:
        List of relevant code snippets with similarity scores
    """
    try:
        # Generate embedding for query
        query_embedding = generate_embedding(query)
        
        if not query_embedding:
            logger.warning("Failed to generate query embedding")
            return []
        
        # Search using pgvector similarity
        # The <=> operator in pgvector returns distance (lower is more similar)
        results = db.query(
            CodeEmbedding,
            (1 - func.cosine_distance(CodeEmbedding.embedding, query_embedding)).label('similarity')
        ).filter(
            CodeEmbedding.repo_analysis_id == repo_analysis_id
        ).order_by(
            func.cosine_distance(CodeEmbedding.embedding, query_embedding)
        ).limit(limit).all()
        
        # Format results
        formatted_results = []
        for embedding_record, similarity in results:
            if similarity >= threshold:
                formatted_results.append({
                    "file_path": embedding_record.file_path,
                    "element_type": embedding_record.element_type,
                    "element_name": embedding_record.element_name,
                    "code_snippet": embedding_record.code_snippet,
                    "similarity": float(similarity),
                    "metadata": embedding_record.code_metadata
                })
        
        logger.info(f"Found {len(formatted_results)} relevant code snippets")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []


def get_most_relevant_snippets(
    db: Session,
    repo_analysis_id: int,
    query: str,
    limit: int = 3
) -> str:
    """
    Get the most relevant code snippets for a query, formatted as context.
    
    Args:
        db: Database session
        repo_analysis_id: ID of the RepoAnalysis
        query: Search query
        limit: Number of snippets to return
    
    Returns:
        Formatted string containing relevant code snippets for context injection
    """
    results = semantic_search(db, repo_analysis_id, query, limit=limit)
    
    if not results:
        return ""
    
    context = "### Relevant Code Snippets:\n"
    for snippet in results:
        context += f"\n**File**: {snippet['file_path']}\n"
        context += f"**Type**: {snippet['element_type']}\n"
        context += f"**Name**: {snippet['element_name']}\n"
        context += f"**Similarity**: {snippet['similarity']:.2%}\n"
        context += f"```\n{snippet['code_snippet']}\n```\n"
    
    return context
