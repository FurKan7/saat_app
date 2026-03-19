"""VLM service — attribute extraction + text reading (Stage C).
Uses Qwen 3.5 Vision (e.g. Qwen/Qwen3.5-2B) via unsloth when available,
with a transformers fallback.
"""
import torch
import json
import re
from PIL import Image
from typing import Dict, Optional, Tuple, Any

# Default: Qwen 3.5 Vision 2B (same as in the reference Gradio script)
VLM_MODEL_NAME = "Qwen/Qwen3.5-2B"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_vlm_model = None
_vlm_processor = None  # tokenizer when unsloth, processor when transformers
_vlm_backend: Optional[str] = None  # "unsloth" | "transformers"
_vlm_load_attempted = False


def get_vlm_model() -> Tuple[Any, Any]:
    """Load VLM (Qwen 3.5 Vision). Prefer unsloth FastVisionModel; fallback to transformers."""
    global _vlm_model, _vlm_processor, _vlm_backend, _vlm_load_attempted
    if _vlm_model is not None:
        return _vlm_model, _vlm_processor
    if _vlm_load_attempted:
        return _vlm_model, _vlm_processor
    _vlm_load_attempted = True

    # 1) Try unsloth FastVisionModel (matches the reference script)
    try:
        from unsloth import FastVisionModel
        print(f"[VLM] Loading {VLM_MODEL_NAME} (unsloth FastVisionModel) on {DEVICE} …")
        _vlm_model, _vlm_processor = FastVisionModel.from_pretrained(
            VLM_MODEL_NAME,
            load_in_4bit=False,
            use_gradient_checkpointing="unsloth",
        )
        FastVisionModel.for_inference(_vlm_model)
        _vlm_model = _vlm_model.to(DEVICE).eval()
        _vlm_backend = "unsloth"
        print("[VLM] Loaded ✓ (unsloth)")
        return _vlm_model, _vlm_processor
    except Exception as e:
        print(f"[VLM] Unsloth load failed: {e}")
        _vlm_model = None
        _vlm_processor = None

    # 2) Fallback: transformers AutoModelForImageTextToText + AutoProcessor
    model_cls = None
    for cls_name in ("AutoModelForImageTextToText", "AutoModelForVision2Seq"):
        try:
            import transformers
            model_cls = getattr(transformers, cls_name, None)
            if model_cls is not None:
                break
        except Exception:
            pass
    if model_cls is None:
        try:
            from transformers import AutoModelForImageTextToText as model_cls
        except ImportError:
            try:
                from transformers import AutoModelForVision2Seq as model_cls
            except ImportError:
                print("[VLM] Disabled — no suitable model class found")
                return None, None

    try:
        try:
            from transformers import AutoProcessor
        except Exception:
            from transformers.models.auto.processing_auto import AutoProcessor
        print(f"[VLM] Loading {VLM_MODEL_NAME} (transformers {model_cls.__name__}) on {DEVICE} …")
        _vlm_processor = AutoProcessor.from_pretrained(VLM_MODEL_NAME)
        dtype = torch.bfloat16 if DEVICE == "cuda" else torch.float32
        attn = "flash_attention_2" if DEVICE == "cuda" else "eager"
        _vlm_model = model_cls.from_pretrained(
            VLM_MODEL_NAME, torch_dtype=dtype, _attn_implementation=attn,
        ).to(DEVICE).eval()
        _vlm_backend = "transformers"
        print("[VLM] Loaded ✓ (transformers)")
    except Exception as e:
        print(f"[VLM] Transformers load failed: {e}")
        _vlm_model = None
        _vlm_processor = None
    return _vlm_model, _vlm_processor


def _vlm_generate(image: Image.Image, prompt: str, max_new_tokens: int = 300) -> str:
    """Run VLM on image + prompt and return decoded text. Works for both unsloth and transformers."""
    model, proc = get_vlm_model()
    if model is None or proc is None:
        return ""

    messages = [
        {"role": "user", "content": [
            {"type": "image"},
            {"type": "text", "text": prompt},
        ]}
    ]

    if _vlm_backend == "unsloth":
        input_text = proc.apply_chat_template(messages, add_generation_prompt=True)
        inputs = proc(
            image,
            input_text,
            add_special_tokens=False,
            return_tensors="pt",
        ).to(DEVICE)
        prompt_len = inputs.input_ids.shape[1]
        with torch.inference_mode():
            ids = model.generate(**inputs, max_new_tokens=max_new_tokens, use_cache=True)
        # Decode only the new tokens (skip prompt)
        if ids.shape[1] > prompt_len:
            ids = ids[:, prompt_len:]
        raw = proc.batch_decode(ids, skip_special_tokens=True)
        return (raw[0] if raw else "").strip()
    else:
        # transformers: processor(text=prompt, images=[image])
        prompt_str = proc.apply_chat_template(messages, add_generation_prompt=True)
        if isinstance(prompt_str, list):
            prompt_str = proc.decode(prompt_str, skip_special_tokens=True)
        inputs = proc(text=prompt_str, images=[image], return_tensors="pt").to(DEVICE)
        with torch.inference_mode():
            ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
        raw = proc.batch_decode(ids, skip_special_tokens=True)
        return (raw[0] if raw else "").strip()


# ── Robust JSON extraction ──────────────────────────────────────────

def _strip_assistant_prefix(text: str) -> str:
    """Remove common chat-style prefixes so we can parse JSON or use plain text."""
    if not text or not text.strip():
        return text
    t = text.strip()
    for prefix in (
        "Assistant:", "assistant:", "ASSISTANT:",
        "Human:", "human:",
        "assistant\n", "Assistant\n",
    ):
        if t.startswith(prefix):
            t = t[len(prefix):].strip()
            break
    # Qwen/SmolVLM sometimes add tags
    if t.startswith("<|im_end|>"):
        t = t.replace("<|im_end|>", "").strip()
    return t


def _parse_json_response(text: str) -> Optional[Dict]:
    """Multiple strategies to extract JSON from VLM output."""
    text = _strip_assistant_prefix(text)
    # 1) balanced-brace match — but prefer the LAST valid JSON object in the string
    depth = 0
    start = None
    last_ok: Optional[Dict] = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    candidate = json.loads(text[start:i + 1])
                    last_ok = candidate  # keep going; we want the final JSON block
                except json.JSONDecodeError:
                    pass
    if last_ok is not None:
        return last_ok

    # 2) regex + common fixups
    matches = list(re.finditer(r'\{.*?\}', text, re.DOTALL))
    if matches:
        # Try from last to first, to prefer the final JSON object (the actual answer)
        for m in reversed(matches):
            raw = m.group(0)
            parsed_here = None
            for fixer in [
                lambda s: s,
                lambda s: re.sub(r',\s*}', '}', s),
                lambda s: s.replace("'", '"'),
                lambda s: re.sub(r'"\s*\n\s*"', '",\n"', s),
                lambda s: re.sub(r'(\w)"(\s*\n\s*")', r'\1",\2', s),
            ]:
                try:
                    parsed_here = json.loads(fixer(raw))
                    break
                except json.JSONDecodeError:
                    continue
            if parsed_here is not None:
                return parsed_here

        # 3) key-value extraction as last resort, also preferring the last match
        raw = matches[-1].group(0)
        for fixer in [
            lambda s: s,
            lambda s: re.sub(r',\s*}', '}', s),
            lambda s: s.replace("'", '"'),
            lambda s: re.sub(r'"\s*\n\s*"', '",\n"', s),
            lambda s: re.sub(r'(\w)"(\s*\n\s*")', r'\1",\2', s),
        ]:
            try:
                return json.loads(fixer(raw))
            except json.JSONDecodeError:
                continue

        # 4) key-value extraction as last resort on the last JSON-looking block
        result: Dict = {}
        for key in ("brand_guess", "dial_color", "bracelet_material", "confidence", "short_explanation"):
            km = re.search(rf'"{key}"\s*:\s*"([^"]*)"', raw)
            if km:
                result[key] = km.group(1)
            else:
                km = re.search(rf'"{key}"\s*:\s*([\d.]+)', raw)
                if km:
                    result[key] = float(km.group(1))
        if result:
            return result

    return None


_EMPTY_ATTRS = {
    "brand_guess": None,
    "dial_color": None,
    "bracelet_material": None,
    "confidence": 0.0,
    "short_explanation": "",
}


# ── Public API ──────────────────────────────────────────────────────

def extract_attributes(image: Image.Image, context_text: Optional[str] = None) -> Dict[str, any]:
    """Extract watch attributes as structured dict."""
    if get_vlm_model()[0] is None:
        return {**_EMPTY_ATTRS, "short_explanation": "VLM not available"}

    ctx = ""
    if context_text and context_text.strip():
        ctx = f"\nDetected text on the watch: {context_text.strip()}\n"

    task = (
        f"Analyze this watch image and return a JSON object with these keys:{ctx}\n"
        '{"brand_guess":"…","dial_color":"…","bracelet_material":"…","confidence":0.0,"short_explanation":"…"}\n'
        "You must respond with exactly one line: only this JSON object, no other text, no markdown, no explanation."
    )

    try:
        generated = _vlm_generate(image, task, max_new_tokens=300)
        generated = _strip_assistant_prefix(generated)
        print(f"[VLM] Attributes raw: {generated[-400:]}")

        parsed: Optional[Dict] = None
        # First, try to parse the whole string as JSON (Qwen often returns pure JSON)
        stripped = generated.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                parsed = json.loads(stripped)
            except Exception:
                parsed = None
        # Fallback to robust parser if that failed
        if parsed is None:
            parsed = _parse_json_response(generated)

        if parsed:
            return {
                "brand_guess": parsed.get("brand_guess"),
                "dial_color": parsed.get("dial_color"),
                "bracelet_material": parsed.get("bracelet_material"),
                "confidence": float(parsed.get("confidence", 0.0)),
                "short_explanation": parsed.get("short_explanation", ""),
            }
        return {**_EMPTY_ATTRS, "short_explanation": f"Could not parse: {generated[-150:]}"}
    except Exception as e:
        print(f"[VLM] Extraction error: {e}")
        return {**_EMPTY_ATTRS, "short_explanation": f"VLM error: {e}"}


def read_text_from_crop(image: Image.Image) -> str:
    """Read text from a tight brand/text crop."""
    if get_vlm_model()[0] is None:
        return ""

    task = "Read the text visible in this image. Return ONLY the text, nothing else."

    try:
        out = _vlm_generate(image, task, max_new_tokens=50)
        out = _strip_assistant_prefix(out)

        lines = [l.strip() for l in out.split("\n") if l.strip()]
        result = lines[-1] if lines else out
        print(f"[VLM] Text read: '{result}'")
        return result
    except Exception as e:
        print(f"[VLM] Text read error: {e}")
        return ""


def verify_candidate(query_image: Image.Image, candidate_image: Image.Image) -> float:
    """Compare query vs candidate using embeddings."""
    try:
        from embedder import embed_image, cosine_similarity
        q = embed_image(query_image, crop_first=True)
        c = embed_image(candidate_image, crop_first=True)
        return cosine_similarity(q, c)
    except Exception as e:
        print(f"[VLM] Verification error: {e}")
        return 0.0
