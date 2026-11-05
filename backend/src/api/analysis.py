from fastapi import APIRouter, BackgroundTasks, Header, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from fastapi.concurrency import run_in_threadpool
import asyncio
import os
import shutil
from src.services.analysis.ast_parser import parse_code
from src.services.analysis.per_file_graph_builder import build_per_file_graph, build_call_graph
from src.services.analysis.summarizer import analyze_code
from src.services.utilities.git_utils import get_repo_git_analysis, is_repo_private, branch_exists, clone_repo_shallow
from src.services.ai.ask_ai import askAI, reset_chat_history
from src.core.security import verify_token, require_auth, TokenData
from src.core.database import get_db
from src.models.database import RepoAnalysis, UserAnalysisHistory
from src.middleware.rate_limiter import limiter
from src.core.logging import get_logger
from sqlalchemy.orm import Session, joinedload
import traceback
from fastapi import Request
from src.tasks.worker import app as celery_app
from src.schemas.requests import AskRequest, RepoRequest, FileGraphRequest, VerifyRequest

router = APIRouter()
logger = get_logger(__name__)


async def get_current_user_from_header(authorization: Optional[str] = Header(None)):
    """
    Extract and verify user from Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer token)
    
    Returns:
        User ID and token data if valid, None otherwise
    """
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            return None
        
        token = authorization[7:]
        token_data = verify_token(token)
        
        return token_data if token_data else None
    except Exception as e:
        logger.warning(f"Error extracting user from token: {e}")
        return None


# === Routes ===



@router.post("/api/verify")
async def verify_repo_branch(req: VerifyRequest):
    """
    Verify if the given repository is public and if the specified branch exists.
    """
    try:
        is_private_task = asyncio.create_task(run_in_threadpool(is_repo_private, req.repo_url))
        branch_exists_task = asyncio.create_task(run_in_threadpool(branch_exists, req.repo_url, req.branch))
        
        is_private, does_branch_exist = await asyncio.gather(is_private_task, branch_exists_task)

        if is_private:
            return {"success": False, "error": "Repository is private or inaccessible. Please ensure it is public."}

        if not does_branch_exist:
            return {"success": False, "error": f"Branch '{req.branch}' does not exist in the repository."}

        return {"success": True, "message": "Repository URL and branch are valid."}

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "error": str(e)}



@router.post("/api/analyze")
@limiter.limit("5/minute")
async def get_ast(
    req: RepoRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Analyze a GitHub repository asynchronously using Celery.
    """
    request_id = req.request_id
    user_id: Optional[int] = None
    
    try:
        logger.info(f"Analysis request: repo={req.repo_url}, branch={req.branch}, request_id={request_id}")
        
        # Extract user from Authorization header if provided
        if authorization:
            token_data = await get_current_user_from_header(authorization)
            if token_data:
                user_id = token_data.user_id
                logger.info(f"Analysis requested by user: {token_data.email} (user_id={user_id})")
        
        # Queue the analysis task (pass user_id for history tracking)
        task = celery_app.send_task(
            'analyze_repository',
            args=[req.repo_url, req.branch, request_id, user_id],
            task_id=request_id
        )
        
        logger.info(f"Analysis task queued: task_id={request_id}, user_id={user_id}")
        
        return {
            "task_id": request_id,
            "status": "queued",
            "message": "Analysis task has been queued and will be processed shortly."
        }
        
    except Exception as e:
        logger.error(f"Error queuing analysis task: {e}", exc_info=True)
        return {
            "error": str(e),
            "task_id": request_id
        }


@router.get("/api/analyze/status/{task_id}")
async def get_analysis_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the status of a repository analysis task.
    
    Args:
        task_id: The task ID returned from /api/analyze
        db: Database session
    
    Returns:
        Dictionary with task status and results (if completed)
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            return {"status": "pending", "task_id": task_id}
        
        elif task.state == 'PROGRESS':
            return {
                "status": "in-progress",
                "task_id": task_id,
                "progress": task.info.get('status', 'Processing...')
            }
        
        elif task.state == 'SUCCESS':
            result = task.result
            logger.info(f"Task {task_id} completed successfully")
            
            return {
                "status": "completed",
                "task_id": task_id,
                "result": result
            }
        
        elif task.state == 'FAILURE':
            logger.error(f"Task {task_id} failed: {task.info}")
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(task.info)
            }
        
        else:
            return {
                "status": task.state.lower(),
                "task_id": task_id
            }
    
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        return {
            "status": "error",
            "task_id": task_id,
            "error": str(e)
        }



@router.post("/api/file")
async def generate_file_graph(
    req: FileGraphRequest,
    authorization: Optional[str] = Header(None)
):
    # Check if user is authenticated
    is_authenticated = False
    if authorization:
        token_data = await get_current_user_from_header(authorization)
        if token_data:
            is_authenticated = True
            logger.info(f"File analysis with AI requested by: {token_data.email}")

    file_graph_task = asyncio.create_task(run_in_threadpool(build_per_file_graph, req.file_path, req.file_ast))
    call_graph_task = asyncio.create_task(run_in_threadpool(build_call_graph, req.file_ast))
    analysis_task = asyncio.create_task(run_in_threadpool(analyze_code, req.repo_url, req.branch, req.file_path, is_authenticated))

    file_graph, call_graph, analysis = await asyncio.gather(file_graph_task, call_graph_task, analysis_task)

    return {
        "file_path": req.file_path,
        "file_graph": file_graph,
        "call_graph": call_graph,
        "analysis": analysis
    }


@router.get("/api/analysis/{repo_analysis_id}")
async def get_analysis_by_id(
    repo_analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific repository analysis by ID.
    This is useful for loading past analyses from user history.
    
    Args:
        repo_analysis_id: ID of the RepoAnalysis record
        db: Database session
    
    Returns:
        Dictionary with repo_analysis and git_analysis data
    """
    try:
        analysis = db.query(RepoAnalysis).filter(
            RepoAnalysis.id == repo_analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "id": analysis.id,
            "repo_url": analysis.repo_url,
            "branch": analysis.branch,
            "repo_analysis": analysis.repo_analysis,
            "git_analysis": analysis.git_analysis,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "updated_at": analysis.updated_at.isoformat() if analysis.updated_at else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/user/history")
async def get_user_history(
    user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get analysis history for the authenticated user.
    
    Args:
        user: Authenticated user data from token
        db: Database session
    
    Returns:
        List of analysis history records with repository and analysis details
    """
    try:
        logger.info(f"Fetching history for user: {user.email} (user_id={user.user_id})")
        # Load only the columns the list needs; the JSON analysis blobs on
        # repo_analysis can be megabytes each, so don't pull them per row.
        history_records = (
            db.query(UserAnalysisHistory)
            .options(
                joinedload(UserAnalysisHistory.repo_analysis).load_only(
                    RepoAnalysis.id, RepoAnalysis.repo_url, RepoAnalysis.branch
                )
            )
            .filter(UserAnalysisHistory.user_id == user.user_id)
            .order_by(UserAnalysisHistory.analyzed_at.desc())
            .all()
        )
        
        logger.info(f"Found {len(history_records)} history records for user {user.user_id}")
        
        history_list = []
        for record in history_records:
            repo_analysis = record.repo_analysis
            history_entry = {
                "id": record.id,
                "repo_url": repo_analysis.repo_url,
                "branch": repo_analysis.branch,
                "analyzed_at": record.analyzed_at.isoformat() if record.analyzed_at else None,
                "notes": record.notes,
                "repo_analysis_id": repo_analysis.id
            }
            history_list.append(history_entry)
        
        return {"history": history_list}
    
    except Exception as e:
        logger.error(f"Error retrieving user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/user/history/notes")
async def update_history_notes(
    history_id: int,
    notes: str,
    user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Update notes for an analysis history record.
    
    Args:
        history_id: ID of the history record
        notes: New notes to save
        user: Authenticated user data from token
        db: Database session
    
    Returns:
        Success/error message
    """
    try:
        history = db.query(UserAnalysisHistory).filter(
            UserAnalysisHistory.id == history_id,
            UserAnalysisHistory.user_id == user.user_id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="History record not found")
        
        history.notes = notes
        db.commit()
        
        return {"message": "Notes updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ask")
async def ask_route(
    req: AskRequest,
    user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    AI-powered code assistant endpoint (REQUIRES AUTHENTICATION).
    Only logged-in users can access AI assistant features.
    
    Features:
    - Maintains conversation context across requests via Redis
    - 1-hour TTL for chat sessions (auto-cleanup)
    - Optional history reset for starting fresh conversations
    - Semantic search for relevant code snippets (if repo_analysis_id provided)
    
    Args:
        req: AskRequest with question, code, history_id, reset flag, and optional repo_analysis_id
        user: Authenticated user data from token
        db: Database session
    
    Returns:
        Dictionary with answer, history_id, and optional error
    """
    logger.info(f"AI assistant request from user: {user.email}")
    history_id = req.history_id or f"{user.user_id}-{req.question[:20]}-{hash(req.code)}"

    if req.reset:
        logger.info(f"History reset requested for user {user.user_id}")
        reset_chat_history(history_id)
        return {"message": "Conversation history reset. Start fresh!"}

    response = await run_in_threadpool(askAI, req.question, req.code, history_id)
    return response
