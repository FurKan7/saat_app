"""
Background ingestion for user collection items.

Rules (v1):
1. If watch exists in `watch_core` (matched by strong identifiers), link it to the user_collection_item only.
2. If not exists, create `watch_suggestions` and run AI extraction to fill `ai_output_json`.

This runs inside a background thread (dev-friendly). For production, replace with a real job queue.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    UserCollection,
    UserCollectionItem,
    WatchCore,
    WatchSuggestion,
    WatchSpecState,
)
from app.ai_helpers import safe_ai_imports


def _get_static_dir() -> Path:
    # apps/api/app/services/... -> apps/api/app -> apps/api -> apps -> repo root
    # main.py uses: Path(__file__).parent.parent / "static"
    return Path(__file__).resolve().parents[2] / "static"


def _image_url_to_path(image_url: str) -> Path:
    """
    Convert a browser URL like `/static/uploads/<file>` into an on-disk path.
    Falls back to returning a path under the static dir.
    """
    static_dir = _get_static_dir()
    u = (image_url or "").strip()
    if u.startswith("/"):
        u = u[1:]
    # If browser path includes `/static/...`, drop the leading `static/` segment
    if u.startswith("static/"):
        u = u[len("static/"):]
    return static_dir / u


def _match_watch_exists(db: Session, item: UserCollectionItem) -> Optional[WatchCore]:
    # Prefer SKU match
    if item.sku:
        return db.query(WatchCore).filter(WatchCore.sku == item.sku).first()

    # Else match by source + product_url
    if item.source and item.product_url:
        return (
            db.query(WatchCore)
            .filter(WatchCore.source == item.source, WatchCore.product_url == item.product_url)
            .first()
        )

    return None


def _write_ai_output_to_suggestion(suggestion: WatchSuggestion, ai_output: dict) -> None:
    suggestion.ai_output_json = ai_output


def _run_ai_extraction(image_path: Path) -> dict:
    """
    Run AI extraction (detector -> VLM).
    We intentionally reuse existing AI modules to keep behavior consistent.
    """
    embedder, detector, vlm = safe_ai_imports()
    detect_watch_and_text = detector.detect_watch_and_text
    extract_attributes = vlm.extract_attributes
    read_text_from_crop = vlm.read_text_from_crop

    image = Image.open(image_path)
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Stage A: detect + text crops
    det = detect_watch_and_text(image)

    # Read detected text crops (used as context for brand guess)
    detected_text = {}
    for label, crops_list in det.text_crops.items():
        safe = label.replace(" ", "_")
        for idx, (crop_img, _box, _score) in enumerate(crops_list):
            txt = read_text_from_crop(crop_img)
            if txt:
                detected_text[f"{safe}_{idx}"] = txt

    context_parts = [v for k, v in detected_text.items() if v and "brand" in k]
    context = " ".join(context_parts).strip() or None

    # Stage C: extract structured attributes from watch crop
    attrs = extract_attributes(det.watch_crop, context_text=context)
    return {
        "brand_guess": attrs.get("brand_guess"),
        "dial_color": attrs.get("dial_color"),
        "bracelet_material": attrs.get("bracelet_material"),
        "confidence": attrs.get("confidence"),
        "short_explanation": attrs.get("short_explanation"),
        "detected_text": detected_text,
    }


def process_user_collection_item(item_id: int) -> None:
    """
    Entry point for background processing.
    Creates its own DB session.
    """
    db_gen = get_db()
    db: Optional[Session] = next(db_gen, None)
    if db is None:
        return

    try:
        item = db.query(UserCollectionItem).filter(UserCollectionItem.id == item_id).first()
        if not item:
            return

        # 1) Mark processing (idempotent)
        item.status = item.status or "processing_ai"
        db.commit()

        # 2) Existence check
        watch = _match_watch_exists(db, item)
        if watch is not None:
            item.watch_id = watch.watch_id
            item.suggestion_id = None
            item.status = "matched_existing"
            db.commit()
            return

        # 3) Create suggestion
        user_collection = db.query(UserCollection).filter(UserCollection.id == item.collection_id).first()
        suggestion = WatchSuggestion(
            submitted_by=user_collection.user_id if user_collection else None,
            status="pending_admin",
            sku=item.sku,
            source=item.source,
            product_url=item.product_url,
            product_name=item.product_name,
            brand=item.brand,
            image_url=item.image_url,
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)

        item.suggestion_id = suggestion.id
        item.status = "pending_admin"
        db.commit()

        # 4) Run AI extraction and store result
        try:
            image_path = _image_url_to_path(item.image_url)
            ai_output = _run_ai_extraction(image_path)
            _write_ai_output_to_suggestion(suggestion, ai_output)
            db.commit()
        except Exception:
            # Keep suggestion pending_admin so admin can see ai_output_json (possibly null)
            db.commit()

    finally:
        try:
            db_gen.close()
        except Exception:
            pass


def start_background_processing(item_id: int) -> None:
    """
    Spawn a background thread for processing.
    """
    t = threading.Thread(target=process_user_collection_item, args=(item_id,), daemon=True)
    t.start()

