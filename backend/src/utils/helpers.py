"""
Common utility functions used across the application.
"""
from typing import Any, Dict, Optional
import uuid


def generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    return str(uuid.uuid4())


def format_file_path(path: str) -> str:
    """Normalize file path for consistent processing."""
    return path.replace("\\", "/").strip()


def safe_get_dict(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dict with default fallback."""
    if isinstance(d, dict):
        return d.get(key, default)
    return default


def truncate_string(s: str, max_length: int = 500) -> str:
    """Truncate string to max length with ellipsis."""
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s
