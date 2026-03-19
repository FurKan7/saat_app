#!/usr/bin/env python3
"""Run this in your API env (e.g. conda activate saat_app) to verify AI deps."""
import sys
print("Python:", sys.executable)
print("Version:", sys.version)

errors = []
# 1. torch
try:
    import torch
    print("torch:", torch.__version__, "OK")
except ImportError as e:
    errors.append(f"torch: {e}")
    print("torch: MISSING")

# 1b. torchvision (must match torch; fixes "operator torchvision::nms does not exist")
try:
    import torchvision
    print("torchvision:", torchvision.__version__, "OK")
except ImportError as e:
    errors.append(f"torchvision: {e}")
    print("torchvision: MISSING (install: pip install torchvision)")

# 2. transformers
try:
    import transformers
    print("transformers:", transformers.__version__, "OK")
except ImportError as e:
    errors.append(f"transformers: {e}")
    print("transformers: MISSING")
    sys.exit(1)

# 3. AutoModel (embedder/detector)
try:
    from transformers import AutoModel
    print("  AutoModel: OK")
except Exception as e:
    errors.append(f"AutoModel: {e}")
    print(f"  AutoModel: FAIL - {e}")

# 4. CLIPProcessor (embedder uses this; avoids broken AutoProcessor in 4.57)
try:
    from transformers.models.clip.processing_clip import CLIPProcessor
    print("  CLIPProcessor (embedder): OK")
except Exception as e:
    errors.append(f"CLIPProcessor: {e}")
    print(f"  CLIPProcessor: FAIL - {e}")

# 5. AutoProcessor (detector/VLM) - top-level often fails in 4.57
try:
    from transformers import AutoProcessor
    print("  AutoProcessor (top-level): OK")
except Exception as e1:
    try:
        from transformers.models.auto.processing_auto import AutoProcessor
        print("  AutoProcessor (from processing_auto): OK")
    except Exception as e2:
        errors.append(f"AutoProcessor: {e1}")
        print(f"  AutoProcessor: FAIL - {e1}")

if errors:
    print("\nFix by running in THIS environment:")
    print("  pip install --upgrade 'torch' 'transformers>=4.30'")
    sys.exit(1)
print("\nAll OK. Restart the API and try identify again.")
