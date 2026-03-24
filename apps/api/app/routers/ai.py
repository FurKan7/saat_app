"""AI endpoints — watch identification pipeline."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import os
import time
import uuid
import json
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import sys

from app.auth import get_current_user
from app.db import get_db, get_db_or_rest
from app.models import User, WatchCore, WatchEmbedding, WatchSpecState
from app.schemas import (
    AIIdentifyResponse, AIIdentifyCandidate, VLMAttributes,
    DetectionCrop, DebugInfo,
)

_ai_path = str(Path(__file__).parent.parent.parent.parent / "ai")
if _ai_path not in sys.path:
    sys.path.insert(0, _ai_path)

try:
    from embedder import embed_image, embed_text, create_watch_text_payload, load_image_from_url, crop_watch_region
    from normalizer import normalize_spec_key
    from vlm import extract_attributes, verify_candidate, read_text_from_crop
    from detector import detect_watch_and_text, get_available_models, set_active_model
    AI_AVAILABLE = True
    VLM_AVAILABLE = True
    DETECTOR_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    VLM_AVAILABLE = False
    DETECTOR_AVAILABLE = False
    print(f"Warning: AI service not available: {e}")

router = APIRouter(prefix="/ai", tags=["ai"])

UNKNOWN_SIMILARITY_THRESHOLD = 0.5
STATIC_DIR = Path(__file__).parent.parent.parent / "static"
DEBUG_DIR = STATIC_DIR / "debug"


def _cleanup_old_debug(max_age_s: int = 3600):
    """Remove debug directories older than max_age_s seconds."""
    import shutil
    if not DEBUG_DIR.exists():
        return
    now = time.time()
    for p in DEBUG_DIR.iterdir():
        if p.is_dir():
            try:
                age = now - p.stat().st_mtime
                if age > max_age_s:
                    shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass


def _save_annotated_image(image: Image.Image, detections: list, path: str):
    """Draw bounding boxes on image and save."""
    ann = image.copy()
    draw = ImageDraw.Draw(ann)
    for d in detections:
        box = d.get("box", [])
        label = d.get("label", "")
        score = d.get("score", 0)
        if len(box) == 4:
            color = "lime" if "watch" in label else "cyan"
            draw.rectangle(box, outline=color, width=3)
            txt = f"{label} {score:.2f}"
            draw.text((box[0] + 2, box[1] + 2), txt, fill=color)
    ann.save(path, "JPEG", quality=90)


def _save_crops(image, watch_crop, watch_box, watch_score, text_crops, output_dir):
    """Save individual crop images and return metadata list."""
    records = []
    if watch_crop:
        fname = "crop_watch.jpg"
        watch_crop.save(os.path.join(output_dir, fname), "JPEG", quality=90)
        records.append({
            "label": "a watch",
            "filename": fname,
            "box": list(watch_box) if watch_box else [],
            "score": watch_score,
        })
    for label, crops_list in (text_crops or {}).items():
        safe = label.replace(" ", "_")
        for idx, (crop_img, box_t, score_t) in enumerate(crops_list):
            fname = f"crop_{safe}_{idx}.jpg"
            crop_img.save(os.path.join(output_dir, fname), "JPEG", quality=90)
            records.append({
                "label": label,
                "filename": fname,
                "box": list(box_t),
                "score": score_t,
            })
    return records


@router.post("/identify", response_model=AIIdentifyResponse)
async def identify_watch(
    image_url: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    top_k: int = Form(5),
    use_vlm: bool = Form(True),
    detector_model_id: Optional[str] = Form(None),
    db_or_rest: tuple = Depends(get_db_or_rest),
    _current_user: User = Depends(get_current_user),
):
    """
    Watch identification pipeline:
      A) Two-pass detection (watch → crop → brand text). Detector: Grounding DINO or LLMDet (optional detector_model_id).
      B) SigLIP2 embedding + pgvector search
      C) VLM attribute extraction + text reading
    """
    start_time = time.time()
    request_id = uuid.uuid4().hex[:10]
    db, supabase = db_or_rest

    if not image_url and not image_file:
        raise HTTPException(status_code=400, detail="Either image_url or image_file required")

    if not AI_AVAILABLE:
        candidates = []
        if supabase:
            r = supabase.table("watch_core").select("watch_id,brand,product_name,image_url").limit(top_k).execute()
            candidates = [
                AIIdentifyCandidate(
                    watch_id=w["watch_id"], brand=w.get("brand"),
                    product_name=w["product_name"], image_url=w.get("image_url"),
                    similarity_score=0.9 - i * 0.1,
                )
                for i, w in enumerate(r.data or [])
            ]
        elif db:
            watches = db.query(WatchCore).limit(top_k).all()
            candidates = [
                AIIdentifyCandidate(
                    watch_id=w.watch_id, brand=w.brand, product_name=w.product_name,
                    image_url=w.image_url, similarity_score=0.9 - i * 0.1,
                )
                for i, w in enumerate(watches)
            ]
        return AIIdentifyResponse(
            candidates=candidates, is_unknown=False,
            retrieval_time_ms=int((time.time() - start_time) * 1000),
        )

    try:
        req_dir = str(DEBUG_DIR / request_id)
        os.makedirs(req_dir, exist_ok=True)
        _cleanup_old_debug()

        # ── Load image ──────────────────────────────────────────────
        if image_file:
            image = Image.open(BytesIO(await image_file.read()))
            if image.mode != "RGB":
                image = image.convert("RGB")
        elif image_url:
            image = load_image_from_url(image_url)
        else:
            raise HTTPException(status_code=400, detail="No image provided")

        image.save(os.path.join(req_dir, "original.jpg"), "JPEG", quality=90)

        # ── Stage A: Two-pass detection ─────────────────────────────
        detect_start = time.time()
        det = None
        if DETECTOR_AVAILABLE:
            try:
                model_id = None
                if detector_model_id:
                    valid = {m["id"] for m in get_available_models()}
                    if detector_model_id in valid:
                        model_id = detector_model_id
                det = detect_watch_and_text(image, model_id=model_id)
            except Exception as e:
                print(f"[IDENTIFY {request_id}] Detector error: {e}")

        if det is None or det.watch_crop is None:
            from detector import DetectionResult
            w, h = image.size
            cs = min(w, h)
            l, t = (w - cs) // 2, (h - cs) // 2
            det = DetectionResult(
                watch_crop=image.crop((l, t, l + cs, t + cs)),
                watch_box=None, watch_score=0.0,
                text_regions={}, text_scores={}, text_crops={},
            )
        detect_ms = int((time.time() - detect_start) * 1000)

        if det.all_detections:
            _save_annotated_image(image, det.all_detections, os.path.join(req_dir, "annotated.jpg"))

        crop_records = _save_crops(
            image, det.watch_crop, det.watch_box, det.watch_score,
            det.text_crops, req_dir,
        )

        base_url = f"/static/debug/{request_id}"
        detection_crops = [
            DetectionCrop(
                label=cr["label"],
                image_url=f'{base_url}/{cr["filename"]}',
                box=cr["box"],
                score=cr["score"],
            )
            for cr in crop_records
        ]

        # ── Stage B: Embed + DB search ──────────────────────────────
        embed_start = time.time()
        try:
            image_embedding = embed_image(det.watch_crop, crop_first=False)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding error: {e}")
        embed_ms = int((time.time() - embed_start) * 1000)

        embedding_str = "[" + ",".join(map(str, image_embedding.tolist())) + "]"

        db_start = time.time()
        candidates = []
        best_similarity = 0.0

        if supabase is not None:
            try:
                r = supabase.rpc("search_watches_by_embedding", {
                    "embedding_text": embedding_str, "top_k": top_k,
                }).execute()
                for row in (r.data or []):
                    sim = float(row["similarity_score"])
                    best_similarity = max(best_similarity, sim)
                    candidates.append(AIIdentifyCandidate(
                        watch_id=row["watch_id"], brand=row.get("brand"),
                        product_name=row["product_name"], image_url=row.get("image_url"),
                        similarity_score=sim,
                    ))
            except Exception as e:
                print(f"[IDENTIFY {request_id}] Supabase RPC failed: {e}")

        if not candidates and db is not None:
            try:
                query = text("""
                    SELECT we.watch_id, wc.brand, wc.product_name, wc.image_url,
                           1 - (we.embedding <=> :embedding\\:\\:vector) as similarity_score
                    FROM watch_embeddings we
                    JOIN watch_core wc ON we.watch_id = wc.watch_id
                    WHERE we.embedding IS NOT NULL
                    ORDER BY we.embedding <=> :embedding\\:\\:vector
                    LIMIT :top_k
                """)
                result = db.execute(query, {"embedding": embedding_str, "top_k": top_k})
                for row in result:
                    sim = float(row.similarity_score)
                    best_similarity = max(best_similarity, sim)
                    candidates.append(AIIdentifyCandidate(
                        watch_id=row.watch_id, brand=row.brand,
                        product_name=row.product_name, image_url=row.image_url,
                        similarity_score=sim,
                    ))
            except Exception as e:
                print(f"[IDENTIFY {request_id}] SQLAlchemy query failed: {e}")
        db_ms = int((time.time() - db_start) * 1000)
        retrieval_time_ms = embed_ms + db_ms
        is_unknown = best_similarity < UNKNOWN_SIMILARITY_THRESHOLD

        # ── Stage C: VLM ────────────────────────────────────────────
        vlm_attributes = None
        vlm_time_ms = None
        detected_text = {}

        if use_vlm and VLM_AVAILABLE:
            vlm_start = time.time()

            for label, crops_list in det.text_crops.items():
                safe = label.replace(" ", "_")
                for idx, (crop_img, _box, _score) in enumerate(crops_list):
                    txt = read_text_from_crop(crop_img)
                    if txt:
                        detected_text[f"{safe}_{idx}"] = txt

            context_parts = [v for k, v in detected_text.items() if v and "brand" in k]
            context = " ".join(context_parts).strip() or None

            # Heuristic brand guess from detected text (e.g. "WR50M CASIO JAPAN MOV" → "CASIO")
            brand_from_context = None
            if context:
                tokens = context.replace(",", " ").split()
                text_tokens = [t for t in tokens if any(ch.isalpha() for ch in t)]
                alpha_tokens = [t for t in text_tokens if t.isalpha()]
                upper_alpha = [t for t in alpha_tokens if t.upper() == t]
                brand_from_context = (
                    (upper_alpha[0] if upper_alpha else None)
                    or (alpha_tokens[0] if alpha_tokens else None)
                    or (text_tokens[0] if text_tokens else None)
                )

            vlm_attributes = None
            try:
                vlm_attributes = extract_attributes(det.watch_crop, context_text=context)
                if context and (not vlm_attributes.get("brand_guess") or vlm_attributes.get("brand_guess") == "null"):
                    vlm_attributes["brand_guess"] = brand_from_context or context
            except Exception as e:
                print(f"[IDENTIFY {request_id}] VLM error: {e}")
                if context:
                    vlm_attributes = {
                        "brand_guess": brand_from_context or context,
                        "dial_color": None,
                        "bracelet_material": None,
                        "confidence": 0.0,
                        "short_explanation": "VLM failed; brand from detected text.",
                    }
            if vlm_attributes is None and context:
                vlm_attributes = {
                    "brand_guess": brand_from_context or context,
                    "dial_color": None,
                    "bracelet_material": None,
                    "confidence": 0.0,
                    "short_explanation": "",
                }

            # Clean "Assistant:" etc. from detected_text for display
            if detected_text:
                cleaned = {}
                for k, v in detected_text.items():
                    if v and isinstance(v, str):
                        v = v.strip()
                        for prefix in ("Assistant:", "assistant:", "ASSISTANT:"):
                            if v.startswith(prefix):
                                v = v[len(prefix):].strip()
                                break
                        if v:
                            cleaned[k] = v
                detected_text = cleaned

            vlm_time_ms = int((time.time() - vlm_start) * 1000)

        # ── Finalize ────────────────────────────────────────────────
        total_ms = int((time.time() - start_time) * 1000)

        debug_data = {
            "request_id": request_id,
            "detector": {
                "model": getattr(det, "model_id", ""),
                "used": det.used_detector,
                "detections": det.all_detections,
                "time_ms": detect_ms,
            },
            "embedding": {"time_ms": embed_ms},
            "db": {"candidates": len(candidates), "best_score": round(best_similarity, 4), "time_ms": db_ms},
            "vlm": {
                "time_ms": vlm_time_ms,
                "detected_text": detected_text,
                "attributes": vlm_attributes,
            },
            "total_ms": total_ms,
        }
        with open(os.path.join(req_dir, "debug.json"), "w") as f:
            json.dump(debug_data, f, indent=2, default=str)

        debug_info = DebugInfo(
            request_id=request_id,
            annotated_image_url=f"{base_url}/annotated.jpg" if det.all_detections else None,
            debug_json_url=f"{base_url}/debug.json",
            detector_used=det.used_detector,
            models={"detector": getattr(det, "model_id", ""), "embedder": "siglip2/clip", "vlm": "Qwen3.5-2B"},
            timing={"detection_ms": detect_ms, "embedding_ms": embed_ms, "db_ms": db_ms, "vlm_ms": vlm_time_ms, "total_ms": total_ms},
        )

        print(f"[IDENTIFY {request_id}] Done in {total_ms}ms  detect={detect_ms}ms  embed={embed_ms}ms  db={db_ms}ms  vlm={vlm_time_ms}ms")

        return AIIdentifyResponse(
            candidates=candidates,
            vlm_attributes=vlm_attributes,
            is_unknown=is_unknown,
            retrieval_time_ms=retrieval_time_ms,
            vlm_time_ms=vlm_time_ms,
            detection_crops=detection_crops,
            detected_text=detected_text if detected_text else None,
            debug_info=debug_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[IDENTIFY {request_id}] ERROR:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error identifying watch: {e}")


@router.post("/embed_watch_images")
async def embed_watch_images(db: Session = Depends(get_db)):
    if not AI_AVAILABLE:
        return {"message": "AI service not available", "total_watches": 0}

    watches = db.query(WatchCore).filter(WatchCore.image_url.isnot(None)).all()
    embedded_count = 0
    failed_count = 0

    try:
        for watch in watches:
            if not watch.image_url:
                continue
            try:
                url = watch.image_url.split(' ')[0].strip()
                if not url:
                    continue
                img = load_image_from_url(url)
                emb = embed_image(img, crop_first=True)
                emb_str = "[" + ",".join(map(str, emb.tolist())) + "]"

                existing = db.query(WatchEmbedding).filter(
                    WatchEmbedding.watch_id == watch.watch_id,
                    WatchEmbedding.model_name == "siglip2",
                ).first()
                if existing:
                    existing.embedding = emb_str
                    existing.text_payload = None
                else:
                    db.add(WatchEmbedding(
                        watch_id=watch.watch_id, embedding=emb_str,
                        text_payload=None, model_name="siglip2",
                    ))
                embedded_count += 1
                if embedded_count % 50 == 0:
                    db.commit()
                    print(f"Embedded {embedded_count} watch images…")
            except Exception as e:
                failed_count += 1
                print(f"Failed to embed watch {watch.watch_id}: {e}")
                continue

        db.commit()
        return {"message": "Image embedding completed", "total_watches": len(watches), "embedded_count": embedded_count, "failed_count": failed_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error embedding watch images: {e}")


@router.post("/embed_watch_core")
async def embed_all_watches(db: Session = Depends(get_db)):
    if not AI_AVAILABLE:
        return {"message": "AI service not available", "total_watches": 0}

    watches = db.query(WatchCore).all()
    embedded_count = 0

    try:
        for watch in watches:
            specs = {}
            for spec in db.query(WatchSpecState).filter(WatchSpecState.watch_id == watch.watch_id).all():
                if spec.spec_value:
                    specs[spec.spec_key] = spec.spec_value

            payload = create_watch_text_payload(watch.brand, watch.product_name, specs)
            emb = embed_text(payload)
            emb_str = "[" + ",".join(map(str, emb.tolist())) + "]"

            existing = db.query(WatchEmbedding).filter(
                WatchEmbedding.watch_id == watch.watch_id,
                WatchEmbedding.model_name == "siglip2",
            ).first()
            if existing:
                existing.embedding = emb_str
                existing.text_payload = payload
            else:
                db.add(WatchEmbedding(
                    watch_id=watch.watch_id, embedding=emb_str,
                    text_payload=payload, model_name="siglip2",
                ))
            embedded_count += 1
            if embedded_count % 50 == 0:
                db.commit()
                print(f"Embedded {embedded_count} watches…")

        db.commit()
        return {"message": "Embedding completed", "total_watches": len(watches), "embedded_count": embedded_count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error embedding watches: {e}")
