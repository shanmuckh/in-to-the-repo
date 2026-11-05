"""Tests for the single-pass git history helpers (no network needed)."""
import subprocess

import pytest

from src.services.utilities.git_utils import (
    build_file_git_index,
    get_repo_git_analysis,
    read_git_history,
)


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "Tester")
    (tmp_path / "a.py").write_text("x = 1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "first | with pipe")
    (tmp_path / "a.py").write_text("x = 2\n")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "b.py").write_text("y = 1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "second")
    return tmp_path


def test_read_git_history(repo):
    commits = read_git_history(str(repo))
    assert [c["message"] for c in commits] == ["second", "first | with pipe"]
    assert sorted(commits[0]["files"]) == ["a.py", "pkg/b.py"]
    assert commits[1]["files"] == ["a.py"]


def test_build_file_git_index(repo):
    index = build_file_git_index(read_git_history(str(repo)))
    assert index["a.py"]["commit_count"] == 2
    assert index["pkg/b.py"]["commit_count"] == 1
    assert index["a.py"]["recent_commits"][0]["message"] == "second"
    assert index["a.py"]["last_modified"] == index["a.py"]["recent_commits"][0]["date"]


def test_repo_git_analysis(repo):
    result = get_repo_git_analysis(str(repo), "https://github.com/o/r", "main", "req")
    assert result["total_commits_fetched"] == 2
    assert result["most_changed_files"][0] == {"file": "a.py", "changes": 2}
    assert result["top_contributors"] == [{"name": "Tester", "commits": 2}]
