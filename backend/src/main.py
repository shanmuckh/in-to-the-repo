from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import analysis
from src.api import auth_routes
from src.core.database import init_db
from src.middleware.rate_limiter import init_limiter
from src.core.logging import get_logger
import os

# Import models so SQLAlchemy can create tables
from src.models import database as models

logger = get_logger(__name__)

FRONTEND_HOST = os.getenv("FRONTEND_HOST")

app = FastAPI()

# Initialize rate limiter
init_limiter(app)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables when the app starts."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Could not initialize database: {e}")

# Allowed origins for CORS (add your frontend URLs here)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # "https://into-the-repo.vercel.app"
]

if FRONTEND_HOST:
    origins.append(FRONTEND_HOST)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)
app.include_router(auth_routes.router)

@app.get("/")
def read_root():
    return {"message": "Backend is running 🚀"}
