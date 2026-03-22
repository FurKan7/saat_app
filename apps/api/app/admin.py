from __future__ import annotations

import os
from typing import Set

from fastapi import Depends, HTTPException

from app.auth import get_current_user
from app.models import User


def _load_admin_ids() -> Set[str]:
    """
    Single admin (typical):
      ADMIN_SUPABASE_USER_ID=<your Supabase user UUID>

    Optional extra admins:
      ADMIN_SUPABASE_USER_IDS=uuid2,uuid3
    """
    ids: Set[str] = set()
    one = os.getenv("ADMIN_SUPABASE_USER_ID", "").strip()
    if one:
        ids.add(one)
    raw = os.getenv("ADMIN_SUPABASE_USER_IDS", "").strip()
    if raw:
        ids.update(p.strip() for p in raw.split(",") if p.strip())
    return ids


def is_admin_user(user: User) -> bool:
    if getattr(user, "is_admin", False):
        return True
    admin_ids = _load_admin_ids()
    return str(user.supabase_user_id) in admin_ids


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not is_admin_user(current_user):
        raise HTTPException(status_code=403, detail="Admin authorization required")
    return current_user

