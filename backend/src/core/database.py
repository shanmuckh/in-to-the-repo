"""
Database configuration and connection management.
Uses SQLAlchemy as ORM and PostgreSQL as the database.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# Load environment variables
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://repo_user:repo_password@localhost:5432/in_to_the_repo"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency injection for database sessions.
    Use in FastAPI route handlers: async def my_route(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create tables. The pgvector extension is optional: if it isn't installed in
    Postgres, the (currently unused) code_embeddings table is skipped so the rest
    of the app still works.
    """
    from sqlalchemy import text
    vector_ok = True
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    except Exception as e:
        vector_ok = False
        print(f"Notice: pgvector not available, skipping code_embeddings table ({e.__class__.__name__})")

    tables = [
        t for t in Base.metadata.sorted_tables
        if vector_ok or t.name != "code_embeddings"
    ]
    Base.metadata.create_all(bind=engine, tables=tables)

    # Composite index for the commit-SHA cache lookup (create_all won't add it to
    # databases created before the index was declared).
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_repo_analysis_lookup "
            "ON repo_analysis (repo_url, branch, last_commit_sha)"
        ))
