from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.admin import require_admin
from app.db import get_db
from app.models import UserCollectionItem, WatchCore, WatchSuggestion, WatchSpecState, WatchSpecSource
from app.schemas import AdminApproveSuggestionRequest, WatchSuggestionResponse


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/watch-suggestions", response_model=List[WatchSuggestionResponse])
def list_pending_suggestions(
    status: str = "pending_admin",
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    rows = (
        db.query(WatchSuggestion)
        .filter(WatchSuggestion.status == status)
        .order_by(WatchSuggestion.created_at.desc())
        .all()
    )
    return [WatchSuggestionResponse.from_orm(r) for r in rows]


@router.post("/watch-suggestions/{suggestion_id}/approve", response_model=WatchSuggestionResponse)
def approve_suggestion(
    suggestion_id: int,
    payload: AdminApproveSuggestionRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    sug = db.query(WatchSuggestion).filter(WatchSuggestion.id == suggestion_id).first()
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if sug.status != "pending_admin":
        raise HTTPException(status_code=400, detail=f"Suggestion status is {sug.status}")

    # Re-check watch existence by strong identifiers before inserting.
    existing = None
    if sug.sku:
        existing = db.query(WatchCore).filter(WatchCore.sku == sug.sku).first()
    if existing is None and sug.source and sug.product_url:
        existing = (
            db.query(WatchCore)
            .filter(WatchCore.source == sug.source, WatchCore.product_url == sug.product_url)
            .first()
        )

    if existing:
        watch_id = existing.watch_id
    else:
        if not (sug.source and sug.product_url and sug.product_name):
            raise HTTPException(status_code=400, detail="Missing required watch identifiers to create watch_core")

        core = WatchCore(
            source=sug.source,
            product_url=sug.product_url,
            image_url=sug.image_url,
            brand=sug.brand,
            product_name=sug.product_name,
            sku=sug.sku,
        )
        db.add(core)
        db.commit()
        db.refresh(core)
        watch_id = core.watch_id

    ai = sug.ai_output_json or {}
    confidence = ai.get("confidence", 0.0)

    # Create spec state rows (v1 uses the VLM keys)
    def _upsert_spec(spec_key: str, spec_value: Optional[str]) -> None:
        if not spec_value or spec_value == "null":
            return
        existing_spec = (
            db.query(WatchSpecState)
            .filter(WatchSpecState.watch_id == watch_id, WatchSpecState.spec_key == spec_key)
            .first()
        )
        if existing_spec:
            existing_spec.spec_value = spec_value
            existing_spec.unit = None
            existing_spec.source_type = "ai_estimated"
            existing_spec.confidence = confidence
        else:
            db.add(
                WatchSpecState(
                    watch_id=watch_id,
                    spec_key=spec_key,
                    spec_value=spec_value,
                    unit=None,
                    source_type="ai_estimated",
                    confidence=confidence,
                )
            )

        # Traceability: source record (AI)
        existing_source = (
            db.query(WatchSpecSource)
            .filter(
                WatchSpecSource.watch_id == watch_id,
                WatchSpecSource.spec_key == spec_key,
                WatchSpecSource.source_type == "ai",
                WatchSpecSource.source_name == "vlm_qwen_3_5_2b",
                WatchSpecSource.spec_value == spec_value,
            )
            .first()
        )
        if not existing_source:
            db.add(
                WatchSpecSource(
                    watch_id=watch_id,
                    spec_key=spec_key,
                    spec_value=spec_value,
                    unit=None,
                    source_type="ai",
                    source_name="vlm_qwen_3_5_2b",
                    source_url=None,
                )
            )

    _upsert_spec("dial_color", ai.get("dial_color"))
    _upsert_spec("bracelet_material", ai.get("bracelet_material"))
    db.commit()

    # Update suggestion + user collection item linking
    sug.status = "approved"
    sug.admin_notes = payload.admin_notes
    db.commit()

    item = (
        db.query(UserCollectionItem)
        .filter(UserCollectionItem.suggestion_id == sug.id)
        .first()
    )
    if item:
        item.watch_id = watch_id
        item.suggestion_id = sug.id
        item.status = "approved_linked"
        db.commit()

    db.refresh(sug)
    return WatchSuggestionResponse.from_orm(sug)


@router.post("/watch-suggestions/{suggestion_id}/reject", response_model=WatchSuggestionResponse)
def reject_suggestion(
    suggestion_id: int,
    payload: AdminApproveSuggestionRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    sug = db.query(WatchSuggestion).filter(WatchSuggestion.id == suggestion_id).first()
    if not sug:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if sug.status != "pending_admin":
        raise HTTPException(status_code=400, detail=f"Suggestion status is {sug.status}")

    sug.status = "rejected"
    sug.admin_notes = payload.admin_notes
    db.commit()

    item = (
        db.query(UserCollectionItem)
        .filter(UserCollectionItem.suggestion_id == sug.id)
        .first()
    )
    if item:
        item.status = "rejected"
        db.commit()

    db.refresh(sug)
    return WatchSuggestionResponse.from_orm(sug)

