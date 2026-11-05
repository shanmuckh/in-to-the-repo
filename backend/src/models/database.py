"""
SQLAlchemy ORM models for the database.
Defines schemas for: RepoAnalysis, User, UserAnalysisHistory, ChatSession, and CodeEmbedding.
"""
from datetime import datetime
from sqlalchemy import Index, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from src.core.database import Base


class RepoAnalysis(Base):
    """
    Stores cached analysis results for repositories.
    Prevents redundant computation for popular repos.
    Cache is tied to the last commit SHA - only updates when new commits exist.
    """
    __tablename__ = "repo_analysis"

    id = Column(Integer, primary_key=True, index=True)
    repo_url = Column(String(500), nullable=False, index=True)
    branch = Column(String(100), default="main")
    last_commit_sha = Column(String(40), nullable=True, doc="SHA of last commit when analysis was done")
    
    # Cached AST and git analysis as JSONB (fast retrieval)
    repo_analysis = Column(JSON, nullable=True, doc="Cached AST parsing results")
    git_analysis = Column(JSON, nullable=True, doc="Cached git history analysis")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    analysis_histories = relationship("UserAnalysisHistory", back_populates="repo_analysis")
    
    # Composite unique constraint on repo_url + branch + last_commit_sha
    __table_args__ = (
        Index("ix_repo_analysis_lookup", "repo_url", "branch", "last_commit_sha"),
        {'extend_existing': True},
    )

    def __repr__(self):
        return f"<RepoAnalysis(repo_url={self.repo_url}, branch={self.branch}, last_commit_sha={self.last_commit_sha[:7] if self.last_commit_sha else None})>"


class User(Base):
    """
    Stores user information for authentication and tracking.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    analysis_histories = relationship("UserAnalysisHistory", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

    def __repr__(self):
        return f"<User(email={self.email}, username={self.username})>"


class UserAnalysisHistory(Base):
    """
    Tracks analysis history per user.
    Links users to their analysis of repositories.
    """
    __tablename__ = "user_analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    repo_analysis_id = Column(Integer, ForeignKey("repo_analysis.id"), nullable=False, index=True)
    
    # Custom notes by user
    notes = Column(Text, nullable=True)
    
    # Timestamp
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analysis_histories")
    repo_analysis = relationship("RepoAnalysis", back_populates="analysis_histories")

    def __repr__(self):
        return f"<UserAnalysisHistory(user_id={self.user_id}, repo_id={self.repo_analysis_id})>"


class ChatSession(Base):
    """
    Stores chat history for AI conversations with TTL caching via Redis.
    This preserves conversation context across sessions.
    """
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Last code analyzed in this session
    last_code = Column(Text, nullable=True)
    
    # Message history (stored as JSON for flexibility)
    messages = Column(JSON, default=list, doc="List of {role, content} messages")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")

    def __repr__(self):
        return f"<ChatSession(user_id={self.user_id}, session_id={self.session_id})>"


class CodeEmbedding(Base):
    """
    Stores vector embeddings for code snippets (functions, classes, etc).
    Enables semantic search to find relevant code snippets for queries.
    """
    __tablename__ = "code_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    repo_analysis_id = Column(Integer, ForeignKey("repo_analysis.id"), nullable=False, index=True)
    
    # Code metadata
    file_path = Column(String(1000), nullable=False, index=True)
    element_type = Column(String(50), nullable=False, index=True)  # "function", "class", "import", etc.
    element_name = Column(String(500), nullable=False)
    
    # Code content
    code_snippet = Column(Text, nullable=False)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    
    # Vector embedding (1536 dimensions for typical embeddings like Gemini)
    embedding = Column(Vector(1536), nullable=False, index=True)
    
    # Metadata for relevance scoring
    code_metadata = Column(JSON, nullable=True, doc="Additional metadata like complexity, imports, etc")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    repo_analysis = relationship("RepoAnalysis")

    def __repr__(self):
        return f"<CodeEmbedding(file_path={self.file_path}, element_name={self.element_name})>"
