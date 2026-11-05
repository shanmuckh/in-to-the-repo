"""
Pydantic request and response schemas for API endpoints.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class AskRequest(BaseModel):
    """Request schema for /api/ask endpoint."""
    question: str
    code: str
    history_id: Optional[str] = None
    reset: Optional[bool] = False
    repo_analysis_id: Optional[int] = None  # Optional repo context for semantic search


class RepoRequest(BaseModel):
    """Request schema for /api/analyze endpoint."""
    repo_url: str
    branch: str 
    request_id: str


class FileGraphRequest(BaseModel):
    """Request schema for /api/file-graph endpoint."""
    file_path: str
    file_ast: Dict[str, Any]
    repo_url: str
    branch: str


class VerifyRequest(BaseModel):
    """Request schema for /api/verify endpoint."""
    repo_url: str
    branch: str




class AnalyzeResponse(BaseModel):
    """Response schema for /api/analyze endpoint."""
    task_id: str
    status: str
    message: str
