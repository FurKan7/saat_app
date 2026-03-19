"""
Stage A: Zero-shot object detection.
Supports two detector models (switchable):
  - MM GroundingDINO  (rziga/mm_grounding_dino_tiny_o365v1_goldg)
  - LLMDet Tiny       (iSEE-Laboratory/llmdet_tiny)
"""
from __future__ import annotations

import torch
from PIL import Image
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

# Transformers imported lazily in _load_model() so the API can start even if
# transformers is missing or has version quirks (e.g. AutoProcessor).

MODEL_GROUNDING_DINO = "rziga/mm_grounding_dino_tiny_o365v1_goldg"
MODEL_LLMDET = "iSEE-Laboratory/llmdet_tiny"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

WATCH_PROMPT = "a watch"
BRAND_PROMPT = "brand text"

DETECTION_THRESHOLD = 0.27 if DEVICE == "cpu" else 0.3
WATCH_CROP_PADDING_PCT = 0.10

_loaded_models: Dict[str, Tuple[Any, Any]] = {}
_active_model_id: str = MODEL_GROUNDING_DINO


def get_available_models() -> List[Dict[str, str]]:
    return [
        {"id": MODEL_GROUNDING_DINO, "name": "MM GroundingDINO Tiny"},
        {"id": MODEL_LLMDET, "name": "LLMDet Tiny"},
    ]


def set_active_model(model_id: str) -> bool:
    global _active_model_id
    valid_ids = {m["id"] for m in get_available_models()}
    if model_id not in valid_ids:
        print(f"[DETECTOR] Unknown model_id: {model_id}")
        return False
    _active_model_id = model_id
    print(f"[DETECTOR] Active model → {model_id}")
    return True


def _load_model(model_id: str) -> bool:
    if model_id in _loaded_models:
        return True
    try:
        from transformers import AutoConfig, AutoModelForZeroShotObjectDetection
        try:
            from transformers import AutoProcessor
        except Exception:
            from transformers.models.auto.processing_auto import AutoProcessor
        print(f"[DETECTOR] Loading {model_id} on {DEVICE} …")

        config = AutoConfig.from_pretrained(model_id)
        config.tie_word_embeddings = False

        processor = AutoProcessor.from_pretrained(model_id)
        model = AutoModelForZeroShotObjectDetection.from_pretrained(
            model_id, config=config,
        ).to(DEVICE).eval()

        _loaded_models[model_id] = (processor, model)
        print(f"[DETECTOR] {model_id} loaded ✓")
        return True
    except Exception as e:
        print(f"[DETECTOR] Failed to load {model_id}: {e}")
        return False


def _get_bundle(model_id: Optional[str] = None) -> Optional[Tuple[Any, Any]]:
    mid = model_id or _active_model_id
    if _load_model(mid):
        return _loaded_models[mid]
    return None


# ── Result dataclass ────────────────────────────────────────────────

@dataclass
class DetectionResult:
    watch_crop: Image.Image
    watch_box: Optional[Tuple[int, int, int, int]]
    watch_score: float
    text_regions: Dict[str, List[Tuple[int, int, int, int]]]
    text_scores: Dict[str, List[float]]
    text_crops: Dict[str, List[Tuple[Image.Image, Tuple[int, int, int, int], float]]]
    all_detections: List[Dict[str, Any]] = field(default_factory=list)
    used_detector: bool = False
    model_id: str = ""


# ── Helpers ─────────────────────────────────────────────────────────

def _center_crop_fallback(image: Image.Image) -> DetectionResult:
    w, h = image.size
    cs = min(w, h)
    l, t = (w - cs) // 2, (h - cs) // 2
    return DetectionResult(
        watch_crop=image.crop((l, t, l + cs, t + cs)),
        watch_box=None, watch_score=0.0,
        text_regions={}, text_scores={}, text_crops={},
    )


def _crop_with_padding(
    image: Image.Image,
    box: Tuple[int, int, int, int],
    padding_pct: float = 0.10,
) -> Image.Image:
    w, h = image.size
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    pad_w = max(bw * padding_pct, 4)
    pad_h = max(bh * padding_pct, 4)
    left = max(0, int(x1 - pad_w))
    top_ = max(0, int(y1 - pad_h))
    right = min(w, int(x2 + pad_w))
    bottom = min(h, int(y2 + pad_h))
    return image.crop((left, top_, right, bottom))


# ── Single-pass detection (matches app.py detect() exactly) ──────────

def _run_single_pass(
    processor,
    model,
    image: Image.Image,
    prompts: List[str],
    threshold: float,
) -> List[Dict[str, Any]]:
    # Same as app.py: texts = [prompts], processor(images=..., text=...), inference_mode, post_process
    texts = [prompts]
    inputs = processor(images=image, text=texts, return_tensors="pt").to(DEVICE)
    model.to(DEVICE).eval()

    with torch.inference_mode():
        outputs = model(**inputs)

    try:
        results = processor.post_process_grounded_object_detection(
            outputs,
            threshold=threshold,
            target_sizes=[image.size[::-1]],
            text_labels=texts,
        )[0]
        label_key = "text_labels"
    except TypeError:
        results = processor.post_process_grounded_object_detection(
            outputs,
            threshold=threshold,
            target_sizes=[image.size[::-1]],
        )[0]
        label_key = "labels"

    detections: List[Dict[str, Any]] = []
    for box, score, label_raw in zip(
        results["boxes"].cpu(), results["scores"].cpu(), results[label_key],
    ):
        score_val = float(score)
        if score_val < threshold:
            continue

        box_tuple = tuple(int(v) for v in box.tolist())

        if isinstance(label_raw, str):
            name = label_raw
        else:
            try:
                idx = int(label_raw.item()) if hasattr(label_raw, "item") else int(label_raw)
                name = prompts[idx] if 0 <= idx < len(prompts) else f"unknown_{idx}"
            except Exception:
                name = str(label_raw)

        detections.append({
            "label": name,
            "box": list(box_tuple),
            "score": round(score_val, 3),
        })
    return detections


# Single-pass public API (HF-style: detect watch + brand text together)

def detect_watch_and_text(
    image: Image.Image,
    model_id: Optional[str] = None,
    threshold: Optional[float] = None,
) -> DetectionResult:
    """
    Single-pass detection, same pattern as the working app.py:
      texts = [[WATCH_PROMPT, BRAND_PROMPT]]
      inputs = processor(images=image, text=texts, ...)
      outputs = model(**inputs)
      results = processor.post_process_grounded_object_detection(..., text_labels=texts)[0]

    From the results we:
      - pick the highest-scoring \"a watch\" box as the main watch
      - treat all other boxes as text regions (typically \"brand text\")
    """
    use_model = model_id or _active_model_id
    use_threshold = threshold if threshold is not None else DETECTION_THRESHOLD

    bundle = _get_bundle(use_model)
    if bundle is None:
        print("[DETECTOR] No model available → center-crop fallback")
        return _center_crop_fallback(image)

    processor, model = bundle

    print(f"[DETECTOR] Single-pass — model={use_model} | prompts={[WATCH_PROMPT, BRAND_PROMPT]} | threshold={use_threshold}")
    dets = _run_single_pass(processor, model, image, [WATCH_PROMPT, BRAND_PROMPT], use_threshold)
    all_detections: List[Dict[str, Any]] = list(dets)

    text_regions: Dict[str, List[Tuple[int, int, int, int]]] = {}
    text_scores_map: Dict[str, List[float]] = {}
    watch_boxes: List[Tuple[float, Tuple[int, int, int, int]]] = []

    for d in dets:
        label = d["label"]
        box = tuple(d["box"])
        score = float(d["score"])

        if label == WATCH_PROMPT:
            watch_boxes.append((score, box))
        else:
            text_regions.setdefault(label, []).append(box)
            text_scores_map.setdefault(label, []).append(score)

        print(f"  DET  '{label}'  score={score:.2f}  box={box}")

    # Build text crops from the full image (no extra pass)
    text_crops: Dict[str, List[Tuple[Image.Image, Tuple[int, int, int, int], float]]] = {}
    for label, boxes in text_regions.items():
        crops_for_label: List[Tuple[Image.Image, Tuple[int, int, int, int], float]] = []
        for box_t, score_t in zip(boxes, text_scores_map[label]):
            crop_img = _crop_with_padding(image, box_t, padding_pct=0.05)
            crops_for_label.append((crop_img, box_t, score_t))
        if crops_for_label:
            text_crops[label] = crops_for_label

    if watch_boxes:
        watch_boxes.sort(key=lambda x: -x[0])
        best_score, best_box = watch_boxes[0]
        watch_crop = _crop_with_padding(image, best_box, WATCH_CROP_PADDING_PCT)
        print(f"[DETECTOR] Best watch  score={best_score:.2f}  box={best_box}")
        return DetectionResult(
            watch_crop=watch_crop,
            watch_box=best_box,
            watch_score=best_score,
            text_regions=text_regions,
            text_scores=text_scores_map,
            text_crops=text_crops,
            all_detections=all_detections,
            used_detector=True,
            model_id=use_model,
        )

    print("[DETECTOR] No watch detected → center-crop fallback")
    fb = _center_crop_fallback(image)
    fb.all_detections = all_detections
    fb.model_id = use_model
    return fb
