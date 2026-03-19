"""Embedding service for watch identification.

Simplified to use CLIP only (openai/clip-vit-base-patch16) for both image and text
embeddings, matching the HF example you provided.
"""
import torch
from PIL import Image
import numpy as np
from typing import List, Tuple, Optional

CKPT_CLIP = "openai/clip-vit-base-patch16"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_model = None
_image_processor = None
_tokenizer = None
_use_clip = True  # we now always use CLIP


def get_model():
    """Load CLIP (image + text) once and reuse it. Uses AutoModel + CLIPProcessor from clip submodule to avoid AutoProcessor import issues (e.g. transformers 4.57)."""
    global _model, _image_processor, _tokenizer, _use_clip
    if _model is not None:
        return _model, _image_processor, _tokenizer, _use_clip
    try:
        from transformers import AutoModel
        from transformers.models.clip.processing_clip import CLIPProcessor
        print(f"Loading CLIP model {CKPT_CLIP} on {DEVICE}...")
        _model = AutoModel.from_pretrained(CKPT_CLIP).to(DEVICE)
        _model.eval()
        _image_processor = CLIPProcessor.from_pretrained(CKPT_CLIP)
        _tokenizer = _image_processor
        _use_clip = True
        print("✅ CLIP model loaded successfully")
        return _model, _image_processor, _tokenizer, _use_clip
    except ImportError as e:
        raise RuntimeError(
            f"Could not import transformers (AutoModel/CLIPProcessor): {e!s}. "
            "Run: pip install 'torch' 'transformers>=4.30'"
        )
    except Exception as e:
        raise RuntimeError(
            f"Could not load CLIP model {CKPT_CLIP}: {e!s}. "
            "Run: pip install 'torch' 'transformers>=4.30'"
        )


def crop_watch_region(image: Image.Image, use_grounding: bool = False):
    """
    Crop watch region from image.
    Stage A: Detection/Cropping with Grounding DINO (a watch, brand text, other text).
    - If use_grounding=True, runs detector and returns (crop, detection_result).
    - Otherwise returns (center_crop, None).
    """
    if use_grounding:
        try:
            from detector import detect_watch_and_text
            result = detect_watch_and_text(image)
            return result.watch_crop, result
        except Exception as e:
            print(f"Detector fallback: {e}")
    # Center crop fallback
    width, height = image.size
    crop_size = min(width, height)
    left = (width - crop_size) // 2
    top = (height - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size
    return image.crop((left, top, right, bottom)), None


def embed_image(image: Image.Image, crop_first: bool = True) -> np.ndarray:
    """Get embedding for an image (CLIP)."""
    model, image_processor, _, use_clip = get_model()
    if model is None or image_processor is None:
        raise RuntimeError("Model or image processor not loaded.")

    if crop_first:
        image, _ = crop_watch_region(image, use_grounding=False)

    try:
        inputs = image_processor(images=[image], return_tensors="pt").to(model.device)
        with torch.no_grad():
            if use_clip:
                out = model.get_image_features(pixel_values=inputs["pixel_values"])
                # Newer transformers may return BaseModelOutputWithPooling
                if hasattr(out, "pooler_output") and out.pooler_output is not None:
                    image_embeddings = out.pooler_output
                elif hasattr(out, "last_hidden_state"):
                    image_embeddings = out.last_hidden_state[:, 0, :]
                else:
                    image_embeddings = out
            image_embeddings = image_embeddings / image_embeddings.norm(dim=-1, keepdim=True)
        return image_embeddings.cpu().numpy()[0]
    except Exception as e:
        raise RuntimeError(f"Error during image embedding: {str(e)}")


def embed_text(text: str) -> np.ndarray:
    """Get embedding for text (CLIP)."""
    model, _, tokenizer, use_clip = get_model()
    inputs = tokenizer(text=text, return_tensors="pt", padding=True, truncation=True).to(model.device)
    with torch.no_grad():
        out = model.get_text_features(**inputs)
        if hasattr(out, "pooler_output") and out.pooler_output is not None:
            text_features = out.pooler_output
        elif hasattr(out, "last_hidden_state"):
            text_features = out.last_hidden_state[:, 0, :]
        else:
            text_features = out
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    return text_features.cpu().numpy()[0]


def create_watch_text_payload(brand: str | None, product_name: str, specs: dict) -> str:
    """Create text payload for watch embedding."""
    parts = []
    
    if brand:
        parts.append(f"Brand: {brand}")
    
    parts.append(f"Model: {product_name}")
    
    # Add key specs
    spec_descriptions = {
        "case_diameter_mm": "Case diameter",
        "case_thickness_mm": "Case thickness",
        "water_resistance_atm": "Water resistance",
        "movement_type": "Movement",
        "glass_type": "Glass",
        "gender": "Gender",
    }
    
    for spec_key, spec_label in spec_descriptions.items():
        if spec_key in specs and specs[spec_key]:
            value = specs[spec_key]
            parts.append(f"{spec_label}: {value}")
    
    return " | ".join(parts)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_image_from_url(url: str) -> Image.Image:
    """Load image from URL."""
    import httpx
    from io import BytesIO
    
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    
    image = Image.open(BytesIO(response.content))
    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    return image


def load_image_from_file(file_path: str) -> Image.Image:
    """Load image from file path."""
    image = Image.open(file_path)
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image
