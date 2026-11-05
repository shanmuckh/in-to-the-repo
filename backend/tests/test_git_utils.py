"""
Unit tests for git_utils.py module.

Tests repository cloning, git analysis, and git information extraction.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.services.utilities.git_utils import (
    extract_owner_repo,
    clone_repo_shallow,
    get_repo_git_analysis,
    get_file_git_info
)


class TestExtractOwnerRepo:
    """Tests for extract_owner_repo function."""
    
    def test_extract_owner_repo_valid_https_url(self):
        """Test extraction from standard HTTPS GitHub URL."""
        repo_url = "https://github.com/owner/repo"
        owner, repo = extract_owner_repo(repo_url)
        assert owner == "owner"
        assert repo == "repo"
    
    def test_extract_owner_repo_with_git_suffix(self):
        """Test extraction from URL with .git suffix."""
        repo_url = "https://github.com/owner/repo.git"
        owner, repo = extract_owner_repo(repo_url)
        assert owner == "owner"
        assert repo == "repo"
    
    def test_extract_owner_repo_ssh_url(self):
        """Test extraction from SSH URL."""
        repo_url = "git@github.com:owner/repo.git"
        owner, repo = extract_owner_repo(repo_url)
        assert owner == "owner"
        assert repo == "repo"
    
    def test_extract_owner_repo_invalid_url(self):
        """Test that invalid URL raises ValueError."""
        repo_url = "invalid-url"
        with pytest.raises(ValueError):
            extract_owner_repo(repo_url)


class TestCloneRepoShallow:
    """Tests for clone_repo_shallow function."""
    
    def test_clone_repo_with_invalid_url(self):
        """Test that cloning invalid repo raises error."""
        with pytest.raises(Exception):
            clone_repo_shallow("https://github.com/nonexistent/nonexistent-repo-xyz")
    
    @pytest.mark.integration
    def test_clone_repo_valid(self):
        """Integration test: Clone a real small public repository."""
        # Using a small test repo
        clone_path = clone_repo_shallow(
            "https://github.com/octocat/Hello-World",
            "master",
            depth=1
        )
        
        try:
            # Verify clone succeeded
            assert os.path.exists(clone_path)
            assert os.path.exists(os.path.join(clone_path, ".git"))
            
            # Verify we got some files
            files = []
            for root, dirs, filenames in os.walk(clone_path):
                files.extend(filenames)
            assert len(files) > 0
            
        finally:
            # Cleanup
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)


class TestGetRepoGitAnalysis:
    """Tests for get_repo_git_analysis function."""
    
    @pytest.mark.integration
    def test_git_analysis_structure(self):
        """Integration test: Verify git analysis returns expected structure."""
        # Clone a test repo
        clone_path = clone_repo_shallow(
            "https://github.com/octocat/Hello-World",
            "master",
            depth=1
        )
        
        try:
            analysis = get_repo_git_analysis(
                clone_path,
                "https://github.com/octocat/Hello-World",
                "master",
                "test-request-id"
            )
            
            # Verify required fields
            assert "repo" in analysis
            assert "owner" in analysis
            assert "default_branch" in analysis
            assert "total_commits_fetched" in analysis
            assert "most_changed_files" in analysis
            assert "top_contributors" in analysis
            assert "commit_activity_by_day" in analysis
            assert "recent_commits" in analysis
            
            # Verify types
            assert isinstance(analysis["total_commits_fetched"], int)
            assert isinstance(analysis["most_changed_files"], list)
            assert isinstance(analysis["top_contributors"], list)
            assert isinstance(analysis["commit_activity_by_day"], dict)
            assert isinstance(analysis["recent_commits"], list)
            
        finally:
            # Cleanup
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)


class TestGetFileGitInfo:
    """Tests for get_file_git_info function."""
    
    @pytest.mark.integration
    def test_get_file_git_info_with_nonexistent_file(self):
        """Test getting git info for non-existent file."""
        clone_path = clone_repo_shallow(
            "https://github.com/octocat/Hello-World",
            "master",
            depth=1
        )
        
        try:
            info = get_file_git_info(clone_path, "nonexistent/file.py")
            
            # Should return structure even if file doesn't exist
            assert "commit_count" in info
            assert "last_modified" in info
            assert "recent_commits" in info
            assert isinstance(info["commit_count"], int)
            
        finally:
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
