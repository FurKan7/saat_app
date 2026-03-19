"""
Minimal test: exact copy of the working HuggingFace reference detect() function.
Run: python test_detector.py <image_path>
Compares fast vs slow processor to find the quality difference.
"""
import sys
import time
import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
import transformers

print(f"transformers version: {transformers.__version__}")
print(f"torch version: {torch.__version__}")
print(f"device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
print()

image_path = sys.argv[1] if len(sys.argv) > 1 else None
if not image_path:
    print("Usage: python test_detector.py <image_path>")
    sys.exit(1)

image = Image.open(image_path).convert("RGB")
print(f"Image size: {image.size} (w x h)")

model_id = "rziga/mm_grounding_dino_tiny_o365v1_goldg"
prompts = ["a watch", "brand text"]
threshold = 0.3

# Load model once
print(f"\nLoading model {model_id}...")
model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device).eval()
print("Model loaded.\n")


def run_detect(processor, image, prompts, threshold, label):
    """Exact copy of the working HuggingFace reference detect() function."""
    t0 = time.perf_counter()

    texts = [prompts]
    inputs = processor(images=image, text=texts, return_tensors="pt").to(device)

    with torch.inference_mode():
        outputs = model(**inputs)

    results = processor.post_process_grounded_object_detection(
        outputs, threshold=threshold, target_sizes=[image.size[::-1]], text_labels=texts,
    )[0]

    elapsed_ms = (time.perf_counter() - t0) * 1000

    print(f"=== {label} ({elapsed_ms:.0f}ms) ===")
    print(f"  Raw detections: {len(results['boxes'])}")

    annotations = []
    for box, score, label_name in zip(results["boxes"], results["scores"], results["text_labels"]):
        score_val = float(score)
        if score_val < threshold:
            continue
        xmin, ymin, xmax, ymax = [int(v) for v in box.tolist()]
        print(f"  {label_name}: score={score_val:.3f} box=({xmin},{ymin},{xmax},{ymax})")
        annotations.append(((xmin, ymin, xmax, ymax), f"{label_name} {score_val:.2f}"))

    if not annotations:
        print("  No detections above threshold!")

    return annotations


# Test 1: Default processor (fast, as transformers 5.x does by default)
print("--- Test 1: Default processor (fast=auto) ---")
proc_default = AutoProcessor.from_pretrained(model_id)
print(f"  Processor type: {type(proc_default).__name__}")
if hasattr(proc_default, 'image_processor'):
    print(f"  Image processor type: {type(proc_default.image_processor).__name__}")
ann_default = run_detect(proc_default, image, prompts, threshold, "DEFAULT (fast=auto)")
print()

# Test 2: Slow processor (use_fast=False)
print("--- Test 2: Slow processor (use_fast=False) ---")
try:
    proc_slow = AutoProcessor.from_pretrained(model_id, use_fast=False)
    print(f"  Processor type: {type(proc_slow).__name__}")
    if hasattr(proc_slow, 'image_processor'):
        print(f"  Image processor type: {type(proc_slow.image_processor).__name__}")
    ann_slow = run_detect(proc_slow, image, prompts, threshold, "SLOW (use_fast=False)")
except Exception as e:
    print(f"  Failed: {e}")
    ann_slow = []
print()

# Test 3: Explicit image processor size check
print("--- Processor config comparison ---")
for name, proc in [("default", proc_default), ("slow", proc_slow if ann_slow else None)]:
    if proc is None:
        continue
    ip = getattr(proc, 'image_processor', proc)
    print(f"  {name}:")
    for attr in ('size', 'do_resize', 'do_rescale', 'do_normalize', 'image_mean', 'image_std', 'resample'):
        val = getattr(ip, attr, '?')
        print(f"    {attr} = {val}")
print()

# Save annotated images for visual comparison
def save_annotated(image, annotations, path):
    img = image.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except Exception:
        font = ImageFont.load_default()
    colors = {"a watch": "#22c55e", "brand text": "#3b82f6"}
    for (x1, y1, x2, y2), text in annotations:
        label = text.rsplit(" ", 1)[0]
        color = colors.get(label, "#f97316")
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rectangle([x1, max(0, y1 - th - 4), x1 + tw + 6, max(0, y1 - th - 4) + th + 4], fill=color)
        draw.text((x1 + 3, max(0, y1 - th - 4) + 2), text, fill="white", font=font)
    img.save(path)
    print(f"Saved: {path}")

save_annotated(image, ann_default, "test_detect_default.jpg")
if ann_slow:
    save_annotated(image, ann_slow, "test_detect_slow.jpg")

print("\nDone! Compare test_detect_default.jpg vs test_detect_slow.jpg")
