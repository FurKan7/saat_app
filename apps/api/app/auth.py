"""Authentication utilities for Supabase Auth."""
from fastapi import HTTPException, Depends, Header
from typing import Optional
import os
from supabase import create_client, Client
from app.db import get_db
from sqlalchemy.orm import Session
from app.models import User
from uuid import UUID

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from Supabase JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        
        # Verify token with Supabase
        user_data = supabase.auth.get_user(token)
        
        if not user_data or not user_data.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        supabase_user_id = UUID(str(user_data.user.id))
        
        # Get or create user in our database
        user = db.query(User).filter(User.supabase_user_id == supabase_user_id).first()
        
        if not user:
            # Create user record
            user = User(
                supabase_user_id=supabase_user_id,
                username=user_data.user.email,
                display_name=user_data.user.email,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None

