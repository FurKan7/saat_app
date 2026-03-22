"""Authentication utilities for Supabase Auth."""
from fastapi import HTTPException, Depends, Header
from typing import Optional
import os
import httpx
from app.db import get_db
from sqlalchemy.orm import Session
from app.models import User
from uuid import UUID

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()


async def _fetch_user_from_supabase_auth(jwt: str) -> dict:
    """
    Validate the access token by calling Supabase GoTrue (same as curl / auth docs).
    SUPABASE_KEY must be the project's anon (JWT) key from Dashboard → Settings → API,
    matching NEXT_PUBLIC_SUPABASE_ANON_KEY in the web app — not the sb_publishable_ key alone.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    url = f"{SUPABASE_URL}/auth/v1/user"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {jwt}",
                    "apikey": SUPABASE_KEY,
                },
                timeout=15.0,
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Could not reach Supabase Auth: {e!s}")

    if response.status_code != 200:
        detail = "Invalid or expired token"
        try:
            body = response.json()
            detail = (
                body.get("error_description")
                or body.get("msg")
                or body.get("message")
                or body.get("error")
                or detail
            )
        except Exception:
            if response.text:
                detail = response.text[:200]
        raise HTTPException(status_code=401, detail=str(detail))

    data = response.json()
    # GoTrue returns the user object at top level; some clients wrap it
    user = data.get("user") if isinstance(data.get("user"), dict) else data
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Malformed user response from Supabase")
    return user


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from Supabase JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    raw = authorization.replace("Bearer ", "", 1).strip()
    if not raw:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    user_payload = await _fetch_user_from_supabase_auth(raw)
    supabase_user_id = UUID(str(user_payload["id"]))
    email = user_payload.get("email")

    try:
        user = db.query(User).filter(User.supabase_user_id == supabase_user_id).first()

        if not user:
            user = User(
                supabase_user_id=supabase_user_id,
                username=email,
                display_name=email,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User sync failed: {str(e)}")


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None
