import os
import subprocess
import shutil
import requests
from urllib.parse import urlparse
from typing import Dict, Any, Optional, Tuple, List
from dotenv import load_dotenv
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from tempfile import TemporaryDirectory, mkdtemp
from typing import Callable
from src.core.logging import get_logger

logger = get_logger(__name__)

env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

GITHUB_API_BASE = "https://api.github.com"

def extract_owner_repo(repo_url):
    if repo_url.startswith("git@") and ":" in repo_url:  # git@github.com:owner/repo.git
        path = repo_url.split(":", 1)[1]
    else:
        path = urlparse(repo_url).path
    parts = path.strip("/").split("/")
    if len(parts) >= 2:
        owner = parts[0]
        repo = parts[1].removesuffix(".git")
        return owner, repo
    raise ValueError("Invalid GitHub URL format")


def clone_repo_shallow(repo_url: str, branch: str = "main", depth: int = 1, blobless: bool = False) -> str:
    """
    Clone a repository using shallow cloning (--depth) for better performance.
    Returns the path to the cloned repository.
    
    This reduces repository ingestion time by ~90% for large repositories.
    
    Args:
        repo_url: GitHub repository URL
        branch: Branch to clone (default: main)
        depth: Depth of clone history to fetch (default: 1, only latest commit)
        blobless: Use a partial clone (--filter=blob:none) so older commits only
            fetch trees/metadata, not file contents. Makes depth > 1 cheap.
    
    Returns:
        Path to the cloned repository
    
    Raises:
        subprocess.CalledProcessError: If git clone fails
    """
    try:
        # Create temporary directory using mkdtemp() instead of TemporaryDirectory()
        # TemporaryDirectory() auto-deletes when the object is garbage collected,
        # which happens immediately after this function returns
        clone_path = mkdtemp(prefix="repo_clone_")
        
        logger.info(f"Starting shallow clone of {repo_url} with depth={depth}")
        
        # Build git clone command with shallow clone option
        git_url = repo_url if repo_url.endswith(".git") else f"{repo_url}.git"
        
        cmd = [
            "git",
            "clone",
            "--depth", str(depth),
            "--branch", branch,
            "--single-branch",
        ]
        if blobless:
            cmd += ["--filter=blob:none"]
        cmd += [git_url, clone_path]
        
        # Execute git clone
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                cmd,
                result.stdout,
                result.stderr
            )
        
        logger.info(f"Successfully cloned repository to {clone_path}")
        return clone_path
        
    except subprocess.TimeoutExpired:
        logger.error(f"Clone operation timed out for {repo_url}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error during shallow clone: {e}")
        raise


def get_repo_files_from_clone(clone_path: str, file_extensions: Optional[list] = None) -> Dict[str, str]:
    """
    Extract files from a cloned repository.
    Optionally filter by file extensions.
    
    Args:
        clone_path: Path to the cloned repository
        file_extensions: List of extensions to include (e.g., ['.py', '.js', '.ts'])
    
    Returns:
        Dictionary mapping file path to file content
    """
    files_dict = {}
    clone_dir = Path(clone_path)
    
    try:
        # Walk through all files in the cloned directory
        for file_path in clone_dir.rglob("*"):
            if file_path.is_file():
                # Skip git directory and hidden files
                if ".git" in file_path.parts:
                    continue
                
                # Filter by extensions if provided
                if file_extensions:
                    if file_path.suffix not in file_extensions:
                        continue
                
                # Get relative path and file content
                relative_path = str(file_path.relative_to(clone_dir))
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        files_dict[relative_path] = content
                except Exception as e:
                    logger.warning(f"Could not read file {relative_path}: {e}")
        
        return files_dict
        
    except Exception as e:
        logger.error(f"Error extracting files from clone: {e}")
        return files_dict


def get_latest_commit_sha(repo_url: str, branch: str) -> Optional[str]:
    """
    Get the latest commit SHA for a repository branch without cloning.
    Uses GitHub API to fetch the commit information.
    
    Args:
        repo_url: GitHub repository URL
        branch: Branch name
    
    Returns:
        Latest commit SHA string, or None if failed
    """
    try:
        owner, repo = extract_owner_repo(repo_url)
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{branch}"
        headers = {
            "Accept": "application/vnd.github+json"
        }
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            commit_sha = data.get("sha")
            logger.info(f"Latest commit SHA for {repo_url}@{branch}: {commit_sha[:7] if commit_sha else 'None'}")
            return commit_sha
        else:
            logger.warning(f"Failed to get latest commit SHA: Status {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching latest commit SHA: {e}")
        return None


def get_repo_tree(owner, repo, branch):
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    headers = {
        "Accept": "application/vnd.github+json"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["tree"]

def download_file(owner, repo, path, branch):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


_REC = "\x1e"  # separates commits in `git log` output
_FLD = "\x1f"  # separates fields (safe even if commit messages contain "|")


def read_git_history(local_repo_path: str, max_commits: int = 50) -> List[Dict[str, Any]]:
    """
    Read the last `max_commits` commits *and the files each one touched* with a
    single `git log` call (instead of one subprocess per commit / per file).
    """
    fmt = f"{_REC}%H{_FLD}%an{_FLD}%ae{_FLD}%aI{_FLD}%s"
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "log", f"--max-count={max_commits}",
             f"--format={fmt}", "--name-only", "--no-renames"],
            cwd=local_repo_path, capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        logger.warning(f"git log failed: {e}")
        return []
    if result.returncode != 0:
        logger.warning(f"git log failed: {result.stderr.strip()}")
        return []

    commits = []
    for block in result.stdout.split(_REC)[1:]:
        lines = block.strip("\n").split("\n")
        header = lines[0].split(_FLD)
        if len(header) < 5:
            continue
        sha, author, email, date_str, message = header[:5]
        commits.append({
            "sha": sha,
            "author": author,
            "email": email,
            "date": date_str,
            "message": message,
            "files": [l.strip() for l in lines[1:] if l.strip()],
        })
    return commits


def build_file_git_index(commits: List[Dict[str, Any]], recent_per_file: int = 10) -> Dict[str, Dict[str, Any]]:
    """Turn a commit list (newest first) into {path: git_info} in one pass."""
    index: Dict[str, Dict[str, Any]] = {}
    for c in commits:
        for path in c["files"]:
            info = index.get(path)
            if info is None:
                info = index[path] = {"commit_count": 0, "last_modified": c["date"], "recent_commits": []}
            info["commit_count"] += 1
            if len(info["recent_commits"]) < recent_per_file:
                info["recent_commits"].append({
                    "sha": c["sha"], "message": c["message"], "author": c["author"], "date": c["date"],
                })
    return index


def get_file_git_info(local_repo_path: str, filepath: str, branch: str = "HEAD") -> Dict[str, Any]:
    """
    Get git information for a specific file using local git commands.
    
    Args:
        local_repo_path: Path to the locally cloned repository
        filepath: Path to the file relative to repository root
        branch: Branch name (default: HEAD)
    
    Returns:
        Dictionary with commit count, last_modified date, and recent commits for the file
    """
    try:
        # Get the number of commits that touched this file
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD", "--", filepath],
            cwd=local_repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        commit_count = int(result.stdout.strip()) if result.returncode == 0 else 0
        
    except Exception as e:
        logger.warning(f"Failed to get commit count for {filepath}: {e}")
        commit_count = 0
    
    try:
        # Get the last 10 commits for this file
        result = subprocess.run(
            ["git", "log", "-10", "--format=%H|%an|%aI|%s", "--", filepath],
            cwd=local_repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        recent_commits = []
        last_modified = None
        
        if result.returncode == 0 and result.stdout.strip():
            for i, line in enumerate(result.stdout.strip().split('\n')):
                if not line.strip():
                    continue
                
                try:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        sha, author, date_str, message = parts[0], parts[1], parts[2], parts[3]
                        
                        recent_commits.append({
                            "sha": sha,
                            "message": message,
                            "author": author,
                            "date": date_str
                        })
                        
                        if i == 0:
                            last_modified = date_str
                except Exception as e:
                    logger.warning(f"Failed to parse commit line: {e}")
            
        return {
            "commit_count": commit_count,
            "last_modified": last_modified,
            "recent_commits": recent_commits
        }
        
    except Exception as e:
        logger.warning(f"Failed to get git log for {filepath}: {e}")
        return {
            "commit_count": commit_count,
            "last_modified": None,
            "recent_commits": []
        }

def get_repo_git_analysis(
    local_repo_path: str,
    repo_url: str,
    branch: str,
    request_id: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    commits: Optional[List[Dict[str, Any]]] = None,
    max_commits: int = 50,
) -> Dict[str, Any]:
    """
    Summarise recent git history of a local clone.

    Pass `commits` (from read_git_history) to reuse history already read for the
    per-file index; otherwise it is read here with a single `git log` call.
    """
    logger.info(f"Starting git analysis for local repo at {local_repo_path}")

    try:
        owner, repo_name = extract_owner_repo(repo_url)
    except Exception:
        repo_name = Path(local_repo_path).name
        owner = "unknown"

    if commits is None:
        commits = read_git_history(local_repo_path, max_commits)
    if not commits:
        return _get_empty_git_analysis(repo_name, owner, branch)

    total = len(commits)
    if progress_callback:
        if total <= 5:
            progress_callback(f"Seriously, bro? You want me to analyze just {total} commits?")
        elif total < max_commits:
            progress_callback(f"Digging through some history! Found about {total} commits.")
        else:
            progress_callback(f"Lots of commits? Yeah, I don't have all day. I'll just look at the last {max_commits}.")

    commit_activity: Dict[str, int] = defaultdict(int)
    file_activity: Dict[str, int] = defaultdict(int)
    author_stats: Dict[str, int] = defaultdict(int)

    for c in commits:
        try:
            date_key = str(datetime.fromisoformat(c["date"].replace("Z", "+00:00")).date())
        except ValueError:
            date_key = c["date"]
        commit_activity[date_key] += 1
        author_stats[c["author"]] += 1
        for f in c["files"]:
            file_activity[f] += 1

    recent = [
        {"sha": c["sha"], "message": c["message"], "author": c["author"], "date": c["date"]}
        for c in commits[:10]
    ]

    return {
        "repo": repo_name,
        "owner": owner,
        "default_branch": branch,
        "total_commits_fetched": total,
        "most_changed_files": [
            {"file": f, "changes": n}
            for f, n in sorted(file_activity.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ],
        "top_contributors": [
            {"name": a, "commits": n}
            for a, n in sorted(author_stats.items(), key=lambda kv: kv[1], reverse=True)[:5]
        ],
        "commit_activity_by_day": dict(commit_activity),
        "recent_commits": recent,
        "first_commit_date": recent[-1]["date"] if recent else None,
        "last_commit_date": recent[0]["date"] if recent else None,
    }


def _get_empty_git_analysis(repo_name: str, owner: str, branch: str) -> Dict[str, Any]:
    """Return an empty git analysis structure when analysis fails."""
    return {
        "repo": repo_name,
        "owner": owner,
        "default_branch": branch,
        "total_commits_fetched": 0,
        "most_changed_files": [],
        "top_contributors": [],
        "commit_activity_by_day": {},
        "recent_commits": [],
        "first_commit_date": None,
        "last_commit_date": None,
    }


def is_repo_private(repo_url: str) -> bool:
    """
    Checks whether a GitHub repository is private or not.
    Returns True if private, False if public.
    """
    try:
        owner, repo_name = extract_owner_repo(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"

        headers = {
            "Accept": "application/vnd.github+json"
        }
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        response = requests.get(api_url, headers=headers)

        if response.status_code == 404:
            return True  
        elif response.status_code == 200:
            return response.json().get("private", True) 
        else:
            logger.warning(f"Unexpected status code {response.status_code}: {response.text}")
            return True  # Fail-safe: assume private

    except Exception as e:
        logger.error(f"Error checking repo visibility: {e}")
        return True  # Fail-safe


def branch_exists(repo_url: str, branch: str = None) -> bool:
    """
    Checks whether a branch exists in the given GitHub repository.
    Returns True if branch exists, False otherwise.
    """
    logger.debug(f"Checking branch existence for repo: {repo_url}, branch: {branch}")
    try:
        owner, repo_name = extract_owner_repo(repo_url)
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/branches/{branch}"

        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            logger.warning(f"Unexpected status code {response.status_code}: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error checking branch existence: {e}")
        return False

