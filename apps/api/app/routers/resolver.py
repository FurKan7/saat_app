"""Resolver endpoints."""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import WatchCore
from app.services.resolver import resolve_watch_specs

router = APIRouter(prefix="/resolver", tags=["resolver"])


@router.post("/run")
async def run_resolver(
    watch_id: int = Query(..., description="Watch ID to resolve"),
    db: Session = Depends(get_db),
    # TODO: Add admin auth check
):
    """Run resolver for a watch (admin endpoint)."""
    watch = db.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
    if not watch:
        raise HTTPException(status_code=404, detail="Watch not found")

    result = resolve_watch_specs(watch_id, db)

    return {
        "message": "Resolver completed",
        "watch_id": watch_id,
        **result,
    }

