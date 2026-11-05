"""
Redis cache utilities for storing chat history and conversation state.
Enables stateless backend architecture with horizontal scaling capability.
"""
import os
import json
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict, Any
import redis

# Load environment variables
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CHAT_HISTORY_TTL = 3600  # 1 hour TTL for chat sessions

# Create Redis client
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()  # Test connection
    print("✓ Connected to Redis")
except Exception as e:
    print(f"⚠ Warning: Could not connect to Redis: {e}")
    redis_client = None


class RedisCache:
    """
    Wrapper around Redis client for chat history and conversation memory.
    Automatically handles JSON serialization and TTL.
    """
    
    PREFIX_CHAT = "chat:"
    PREFIX_CODE = "code:"
    
    @staticmethod
    def _get_client():
        """Get or reconnect to Redis client."""
        if redis_client is None:
            raise ConnectionError("Redis client not initialized")
        return redis_client
    
    @classmethod
    def set_chat_history(cls, history_id: str, chat_data: Dict[str, Any]) -> bool:
        """
        Store chat history in Redis with TTL.
        
        Args:
            history_id: Unique identifier for the chat session
            chat_data: Dictionary containing chat object and metadata
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{cls.PREFIX_CHAT}{history_id}"
            value = json.dumps(chat_data)
            cls._get_client().setex(key, CHAT_HISTORY_TTL, value)
            return True
        except Exception as e:
            print(f"Error storing chat history: {e}")
            return False
    
    @classmethod
    def get_chat_history(cls, history_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve chat history from Redis.
        
        Args:
            history_id: Unique identifier for the chat session
        
        Returns:
            Dictionary containing chat data, or None if not found
        """
        try:
            key = f"{cls.PREFIX_CHAT}{history_id}"
            value = cls._get_client().get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return None
    
    @classmethod
    def delete_chat_history(cls, history_id: str) -> bool:
        """
        Delete chat history from Redis.
        
        Args:
            history_id: Unique identifier for the chat session
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{cls.PREFIX_CHAT}{history_id}"
            cls._get_client().delete(key)
            return True
        except Exception as e:
            print(f"Error deleting chat history: {e}")
            return False
    
    @classmethod
    def set_last_code(cls, history_id: str, code: str) -> bool:
        """
        Store the last code snippet analyzed in a session.
        
        Args:
            history_id: Unique identifier for the chat session
            code: Code snippet to store
        
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{cls.PREFIX_CODE}{history_id}"
            cls._get_client().setex(key, CHAT_HISTORY_TTL, code)
            return True
        except Exception as e:
            print(f"Error storing last code: {e}")
            return False
    
    @classmethod
    def get_last_code(cls, history_id: str) -> Optional[str]:
        """
        Retrieve the last code snippet analyzed in a session.
        
        Args:
            history_id: Unique identifier for the chat session
        
        Returns:
            Code snippet, or None if not found
        """
        try:
            key = f"{cls.PREFIX_CODE}{history_id}"
            return cls._get_client().get(key)
        except Exception as e:
            print(f"Error retrieving last code: {e}")
            return None
    
    @classmethod
    def exists(cls, history_id: str) -> bool:
        """Check if a chat session exists in Redis."""
        try:
            key = f"{cls.PREFIX_CHAT}{history_id}"
            return cls._get_client().exists(key) > 0
        except Exception as e:
            print(f"Error checking chat existence: {e}")
            return False
