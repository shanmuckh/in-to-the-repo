"""
Celery worker for handling long-running analysis tasks.

This module defines async tasks for repository cloning, parsing, and analysis
that run in background worker processes to prevent blocking the API.
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery
from src.services.utilities.git_utils import (
    clone_repo_shallow, get_repo_git_analysis, get_latest_commit_sha,
    read_git_history, build_file_git_index,
)
from src.services.analysis.ast_parser import parse_code

from src.core.logging import get_logger
from src.core.database import SessionLocal
from src.models.database import RepoAnalysis, UserAnalysisHistory
from typing import Optional, Callable

logger = get_logger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# How much history to fetch. The clone is blobless, so extra depth only costs
# commit/tree metadata, not file contents.
HISTORY_DEPTH = int(os.getenv("GIT_HISTORY_DEPTH", "50"))

# Initialize Celery
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    'in_to_the_repo',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.tasks.worker']
)

# Configure Celery
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    result_expires=3600,  # Results expire after 1 hour
    worker_prefetch_multiplier=1,  # long tasks: don't let one worker hoard the queue
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)


@app.task(name='analyze_repository', bind=True)
def analyze_repository(self, repo_url: str, branch: str, request_id: str, user_id: Optional[int] = None):
    """
    Analyze a GitHub repository asynchronously.
    
    This task:
    1. Clones the repository locally
    2. Parses the code to extract AST
    3. Analyzes git history
    4. Saves results to database
    5. Saves to user history if user_id provided
    6. Returns the combined analysis
    
    Args:
        repo_url: GitHub repository URL
        branch: Branch to analyze
        request_id: Request ID for tracking progress
        user_id: Optional user ID for saving to history
    
    Returns:
        Dictionary with repo_analysis and git_analysis
    """
    db = SessionLocal()
    local_repo_path = None
    
    # Define progress callback
    def progress_callback(message: str):
        self.update_state(state='PROGRESS', meta={'status': message})
        logger.info(f"Progress update for {request_id}: {message}")

    try:
        progress_callback('Initializing scan...')
        logger.info(f"Starting analysis task for {repo_url} (request_id: {request_id})")
        
        # First, get the latest commit SHA to check if we need to re-analyze
        latest_commit_sha = get_latest_commit_sha(repo_url, branch)
        logger.info(f"Latest commit SHA: {latest_commit_sha[:7] if latest_commit_sha else 'None'}")
        
        # Check if we already have analysis for this exact commit
        repo_analysis_id = None
        existing_analysis = None
        
        if latest_commit_sha:
            existing_analysis = db.query(RepoAnalysis).filter(
                RepoAnalysis.repo_url == repo_url,
                RepoAnalysis.branch == branch,
                RepoAnalysis.last_commit_sha == latest_commit_sha
            ).first()
            
            if existing_analysis:
                repo_analysis_id = existing_analysis.id
                repo_analysis = existing_analysis.repo_analysis
                git_analysis = existing_analysis.git_analysis
                logger.info(f"Using cached analysis for {repo_url} at commit {latest_commit_sha[:7]}")
        
        # If no cached analysis, or no commit SHA, do full analysis
        if not existing_analysis:
            logger.info("No cached analysis found, performing full analysis")
            
            # Clone repository (blobless partial clone with recent history)
            progress_callback('Cloning repository...')
            local_repo_path = clone_repo_shallow(repo_url, branch, depth=HISTORY_DEPTH, blobless=True)
            logger.info(f"Cloned {repo_url} to {local_repo_path}")

            # Read history once; reuse it for per-file info and repo-level stats
            commits = read_git_history(local_repo_path, HISTORY_DEPTH)
            file_git_index = build_file_git_index(commits)

            # Parse code
            repo_analysis = parse_code(
                local_repo_path, repo_url, branch, request_id, progress_callback,
                file_git_index=file_git_index,
            )
            logger.info(f"Code parsing complete, found {len(repo_analysis.get('ast', {}))} files")

            progress_callback('Analyze git history...')

            # Get git analysis
            git_analysis = get_repo_git_analysis(
                local_repo_path, repo_url, branch, request_id, progress_callback,
                commits=commits, max_commits=HISTORY_DEPTH,
            )
            logger.info(f"Completed analysis for {repo_url}")
        
            # Save to database with commit SHA
            try:
                # Check if we need to create or update
                existing_any = db.query(RepoAnalysis).filter(
                    RepoAnalysis.repo_url == repo_url,
                    RepoAnalysis.branch == branch
                ).first()
                
                if not existing_any:
                    # Create new repo analysis record
                    analysis_record = RepoAnalysis(
                        repo_url=repo_url,
                        branch=branch,
                        last_commit_sha=latest_commit_sha,
                        repo_analysis=repo_analysis,
                        git_analysis=git_analysis
                    )
                    db.add(analysis_record)
                    db.commit()
                    db.refresh(analysis_record)
                    repo_analysis_id = analysis_record.id
                    logger.info(f"Created new repo analysis with id={repo_analysis_id}")
                else:
                    # Update existing record with new commit data
                    existing_any.last_commit_sha = latest_commit_sha
                    existing_any.repo_analysis = repo_analysis
                    existing_any.git_analysis = git_analysis
                    from datetime import datetime
                    existing_any.updated_at = datetime.now()
                    db.commit()
                    repo_analysis_id = existing_any.id
                    logger.info(f"Updated repo analysis id={repo_analysis_id} with new commit")
            
            except Exception as e:
                logger.error(f"Failed to save analysis to database: {e}")
                db.rollback()
        
        # Always create history entry for user (audit trail - regardless of whether analysis was cached or new)
        if user_id and repo_analysis_id:
            try:
                from src.models.database import UserAnalysisHistory
                
                # Always create a new history entry for each analysis attempt
                history_record = UserAnalysisHistory(
                    user_id=user_id,
                    repo_analysis_id=repo_analysis_id
                )
                db.add(history_record)
                db.commit()
                logger.info(f"Created history entry: user={user_id}, analysis={repo_analysis_id}, commit={latest_commit_sha[:7] if latest_commit_sha else 'None'}")
            except Exception as e:
                logger.error(f"Failed to save history entry: {e}")
                db.rollback()
        
        # Verify repo_analysis_id was obtained
        if repo_analysis_id is None:
            logger.error("repo_analysis_id is None - database save may have failed")
        
        # Mark progress as done before returning
        progress_callback("Putting the final pieces. Hope it was worth the wait (it probably wasn't).")
        
        logger.info(f"Analysis completed for {repo_url}, returning id={repo_analysis_id}")
        
        if repo_analysis_id is None:
            raise RuntimeError("Analysis finished but could not be saved to the database.")

        # Return only the ID: the frontend loads the (large) analysis from
        # /api/analysis/{id}, so there's no point storing it again in Redis.
        return {
            'repo_url': repo_url,
            'branch': branch,
            'request_id': request_id,
            'repo_analysis_id': repo_analysis_id
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error analyzing repository {repo_url}: {e}", exc_info=True)
        tb = traceback.format_exc()
        self.update_state(
            state='FAILURE',
            meta={
                'exc_type': type(e).__name__,
                'exc_message': str(e),
                'exc_module': type(e).__module__,
                'error': str(e),
                'exception_type': type(e).__name__,
                'traceback': tb
            }
        )
        raise
        
    finally:
        # Cleanup temporary repository
        if local_repo_path and os.path.exists(local_repo_path):
            try:
                shutil.rmtree(local_repo_path)
                logger.info(f"Cleaned up temporary repository: {local_repo_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp repo at {local_repo_path}: {e}")
        
        # Close database session
        db.close()
        
        # Clean up progress data after a delay to ensure client gets final message
        # (This is optional but helps prevent memory leakage from old requests)


@app.task(name='clone_repository', bind=True)
def clone_repository(self, repo_url: str, branch: str = 'main'):
    """
    Clone a repository asynchronously.
    
    Args:
        repo_url: GitHub repository URL
        branch: Branch to clone (default: main)
    
    Returns:
        Path to the cloned repository
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Cloning...'})
        logger.info(f"Starting clone task for {repo_url}")
        
        local_repo_path = clone_repo_shallow(repo_url, branch)
        
        logger.info(f"Clone completed: {local_repo_path}")
        return {'local_repo_path': local_repo_path}
        
    except Exception as e:
        logger.error(f"Error cloning repository {repo_url}: {e}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@app.task(name='health_check')
def health_check():
    """
    Simple health check task to verify worker is responding.
    """
    return {'status': 'healthy', 'worker': 'active'}
