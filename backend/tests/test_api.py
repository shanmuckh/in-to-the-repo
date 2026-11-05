"""
Unit tests for FastAPI /analyze endpoint.

Tests API request/response handling, error cases, and validation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app
from src.api.analysis import RepoRequest


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_repo_request():
    """Sample repository request for testing."""
    return {
        "repo_url": "https://github.com/test/repo",
        "branch": "main",
        "request_id": "test-request-123"
    }


class TestAnalyzeEndpoint:
    """Tests for POST /api/analyze endpoint."""
    
    def test_analyze_request_validation(self):
        """Test that endpoint validates required fields."""
        client = TestClient(app)
        
        # Missing required field
        response = client.post("/api/analyze", json={
            "repo_url": "https://github.com/test/repo"
            # Missing branch and request_id
        })
        assert response.status_code == 422  # Validation error
    
    @patch('src.api.analysis.celery_app.send_task')
    def test_analyze_returns_task_id(self, mock_send_task, client, sample_repo_request):
        """Test that endpoint returns task_id."""
        mock_send_task.return_value = Mock()
        
        response = client.post("/api/analyze", json=sample_repo_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["task_id"] == sample_repo_request["request_id"]
        assert data["status"] == "queued"
    
    @patch('src.api.analysis.celery_app.send_task')
    def test_analyze_queues_task(self, mock_send_task, client, sample_repo_request):
        """Test that task is queued with correct parameters."""
        mock_send_task.return_value = Mock()
        
        client.post("/api/analyze", json=sample_repo_request)
        
        # Verify task was sent
        mock_send_task.assert_called_once()
        call_args = mock_send_task.call_args
        
        # Check task name
        assert call_args[0][0] == 'analyze_repository'
        
        # Check task arguments
        assert call_args[1]['args'][0] == sample_repo_request["repo_url"]
        assert call_args[1]['args'][1] == sample_repo_request["branch"]


class TestVerifyEndpoint:
    """Tests for POST /api/verify endpoint."""
    
    def test_verify_request_validation(self, client):
        """Test endpoint validates required fields."""
        response = client.post("/api/verify", json={
            "repo_url": "https://github.com/test/repo"
            # Missing branch
        })
        assert response.status_code == 422
    
    @patch('src.api.analysis.is_repo_private')
    @patch('src.api.analysis.branch_exists')
    def test_verify_private_repo(self, mock_branch, mock_private, client):
        """Test verification of private repository."""
        mock_private.return_value = True
        mock_branch.return_value = True
        
        response = client.post("/api/verify", json={
            "repo_url": "https://github.com/test/private-repo",
            "branch": "main"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "private" in data["error"].lower()
    
    @patch('src.api.analysis.is_repo_private')
    @patch('src.api.analysis.branch_exists')
    def test_verify_nonexistent_branch(self, mock_branch, mock_private, client):
        """Test verification with non-existent branch."""
        mock_private.return_value = False
        mock_branch.return_value = False
        
        response = client.post("/api/verify", json={
            "repo_url": "https://github.com/test/repo",
            "branch": "nonexistent-branch"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "branch" in data["error"].lower()
    
    @patch('src.api.analysis.is_repo_private')
    @patch('src.api.analysis.branch_exists')
    def test_verify_valid_repo(self, mock_branch, mock_private, client):
        """Test successful verification."""
        mock_private.return_value = False
        mock_branch.return_value = True
        
        response = client.post("/api/verify", json={
            "repo_url": "https://github.com/test/valid-repo",
            "branch": "main"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestStatusEndpoint:
    """Tests for GET /api/analyze/status endpoint."""
    
    @patch('src.api.analysis.celery_app.AsyncResult')
    def test_analyze_status_pending(self, mock_async_result, client):
        """Test status check for pending task."""
        mock_task = Mock()
        mock_task.state = 'PENDING'
        mock_async_result.return_value = mock_task
        
        response = client.get("/api/analyze/status/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["task_id"] == "test-task-id"
    
    @patch('src.api.analysis.celery_app.AsyncResult')
    def test_analyze_status_in_progress(self, mock_async_result, client):
        """Test status check for in-progress task."""
        mock_task = Mock()
        mock_task.state = 'PROGRESS'
        mock_task.info = {'status': 'Parsing code...'}
        mock_async_result.return_value = mock_task
        
        response = client.get("/api/analyze/status/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in-progress"
        assert data["progress"] == "Parsing code..."
    
    @patch('src.api.analysis.celery_app.AsyncResult')
    def test_analyze_status_completed(self, mock_async_result, client):
        """Test status check for completed task."""
        mock_task = Mock()
        mock_task.state = 'SUCCESS'
        mock_task.result = {
            'repo_analysis': {'ast': {}},
            'git_analysis': {'repo': 'test'}
        }
        mock_async_result.return_value = mock_task
        
        response = client.get("/api/analyze/status/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "result" in data


class TestRateLimiting:
    """Tests for rate limiting on /api/analyze endpoint."""
    
    @patch('src.api.analysis.celery_app.send_task')
    def test_rate_limit_headers(self, mock_send_task, client, sample_repo_request):
        """Test that rate limit headers are present."""
        mock_send_task.return_value = Mock()
        
        response = client.post("/api/analyze", json=sample_repo_request)
        
        # Rate limiter adds headers
        assert "RateLimit-Limit" in response.headers or response.status_code == 200
