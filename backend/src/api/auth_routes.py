"""
Authentication API routes for user signup, login, and token management.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.database import User, UserAnalysisHistory, RepoAnalysis
from src.core.security import (
    UserCreate,
    UserLogin,
    Token,
    TokenData,
    hash_password,
    verify_password,
    create_access_token,
    get_token_expiry_seconds,
    require_auth
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/signup", response_model=Token)
async def signup(req: UserCreate, db: Session = Depends(get_db)):
    """
    User signup endpoint.
    Creates a new user account and returns JWT access token.
    
    Args:
        req: UserCreate with email, username, password
        db: Database session
    
    Returns:
        Token with access_token and expiry information
    
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == req.email).first()
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == req.username).first()
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = hash_password(req.password)
    new_user = User(
        email=req.email,
        username=req.username,
        hashed_password=hashed_password,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate JWT token
    token_data = {
        "user_id": new_user.id,
        "email": new_user.email,
        "username": new_user.username
    }
    access_token = create_access_token(token_data)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds()
    )


@router.post("/login", response_model=Token)
async def login(req: UserLogin, db: Session = Depends(get_db)):
    """
    User login endpoint.
    Authenticates user and returns JWT access token.
    
    Args:
        req: UserLogin with email and password
        db: Database session
    
    Returns:
        Token with access_token and expiry information
    
    Raises:
        HTTPException: If user not found or password incorrect
    """
    # Find user by email
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )
    
    # Generate JWT token
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "username": user.username
    }
    access_token = create_access_token(token_data)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds()
    )


@router.get("/me")
async def get_current_user(
    user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    Requires Authorization header with Bearer token.
    
    Returns:
        User information
    """
    db_user = db.query(User).filter(User.id == user.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return {
        "id": db_user.id,
        "email": db_user.email,
        "username": db_user.username,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at
    }


@router.get("/history")
async def get_user_history(
    user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get user's analysis history.
    Returns list of repositories analyzed by the user.
    
    Returns:
        List of analysis history entries with repo details
    """
    history = (
        db.query(UserAnalysisHistory)
        .filter(UserAnalysisHistory.user_id == user.user_id)
        .order_by(UserAnalysisHistory.analyzed_at.desc())
        .all()
    )
    
    result = []
    for entry in history:
        repo = db.query(RepoAnalysis).filter(RepoAnalysis.id == entry.repo_analysis_id).first()
        if repo:
            result.append({
                "id": entry.id,
                "repo_url": repo.repo_url,
                "branch": repo.branch,
                "analyzed_at": entry.analyzed_at,
                "notes": entry.notes
            })
    
    return result
