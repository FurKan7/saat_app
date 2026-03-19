# Watch Identification Platform — Technical Report v1

**Document version:** `v1`  
**Date:** 2026-01-26  
**Scope:** End-to-end identification from a watch photo (detect → embed → retrieve → vision-language attributes + text).

---

## 1. Purpose / Goals

This project helps identify a watch by combining:

1. **Vision detection** to localize the watch and relevant text regions.
2. **Vector embedding + similarity search** to retrieve the most similar watches from the database.
3. **Vision-Language Model (VLM)** to infer structured attributes (brand/dial/bracelet) and to read text from detected crops.

The result is returned to the frontend together with annotated debug artifacts.

---

## 2. Versioning (v1)

This report is for the **feature-complete “Identification Milestone”** (v1).

At a higher level the repository is represented as `watch-platform@0.1.0` (root `package.json`), but the **AI pipeline milestone** here is tracked as `v1`.

**v1 assumptions**
* The catalog embeddings exist for the retrieval stage.
* Stage A (detector) can sometimes fall back to a center crop.
* VLM quality depends on runtime environment (CPU vs GPU) and model loading backend (unsloth vs transformers fallback).

---

## 3. Architecture Overview

### 3.1 Components

* **Frontend (Next.js / React Query)**
  * Uploads an image (or accepts image URL)
  * Calls backend `POST /ai/identify`
  * Renders:
    * detected regions (crops)
    * “Detected by AI” attributes
    * matching candidates from retrieval
    * optional debug links

* **Backend (FastAPI)**
  * Orchestrates the entire pipeline in a single request:
    * load/convert image
    * Stage A: detector + crops
    * Stage B: embedding + DB/vector search
    * Stage C: VLM attribute extraction + OCR-like reading
  * Writes per-request debug assets under `apps/api/static/debug/<request_id>/debug.json`

* **AI modules (`apps/ai`)**
  * `detector.py` — watch + text grounding detection and cropping (Stage A)
  * `embedder.py` — CLIP embeddings for similarity retrieval (Stage B)
  * `vlm.py` — Qwen vision-language attribute extraction and text reading (Stage C)

---

## 4. Public API

### 4.1 `POST /ai/identify`
**Input**
* `image_file` (multipart) OR `image_url`
* `top_k` (default `5`)
* `use_vlm` (default `true`)
* `detector_model_id` optional (switches detector backbone)

**Output**
* `candidates`: top matches from similarity search
* `vlm_attributes`: structured attributes inferred by VLM
* `detected_text`: OCR-like text strings extracted from detected text crops
* debug fields (via `debug_info`)

### 4.2 Batch endpoints (embedding preparation)
* `POST /ai/embed_watch_images`
* `POST /ai/embed_watch_core`

These endpoints precompute embeddings to populate the DB for faster identification.

---

## 5. Pipeline (Algorithms & Model Details)

### Stage A — Zero-shot Detection & Cropping

**Goal:** locate:
* the main **watch** region
* **brand text** / other text regions (for later OCR-like reading)

**Model family:** Hugging Face zero-shot grounding detection.

**Implementation: `apps/ai/detector.py`**

**Backbones (switchable)**
* Default: `rziga/mm_grounding_dino_tiny_o365v1_goldg`
* Alternate: `iSEE-Laboratory/llmdet_tiny`

**Detection strategy**
* Prompts are passed as a list:
  * `"a watch"`
  * `"brand text"`
* A **single-pass** forward pass produces all boxes.
* Post-processing:
  * choose highest-scoring `"a watch"` box as the `watch_crop`
  * treat all other boxes as `text_crops` by label

**Cropping logic**
* `watch_crop`: padded crop (padding percentage configurable)
* `text_crops`: smaller padded crop to improve text reading

**Fallback**
* If detector cannot load, returns a **center square crop** as `watch_crop` and skips text regions.

---

### Stage B — Embedding & Retrieval

**Goal:** find similar watches in the catalog by vector similarity.

**Embedding model:** CLIP
* Checkpoint: `openai/clip-vit-base-patch16`

**Implementation: `apps/ai/embedder.py`**

**Embedding logic**
* The watch crop is embedded using CLIP image features.
* Output embedding is L2-normalized and returned as a numpy vector.

**Retrieval**
* If configured, use Supabase RPC vector search (embedding passed as text).
* Otherwise, execute SQL similarity using pgvector distance:
  * `ORDER BY we.embedding <=> :embedding::vector`

**Similarity interpretation**
* The system converts distance into a similarity score.
* If the best score is below `UNKNOWN_SIMILARITY_THRESHOLD` (0.5), the response flags `is_unknown`.

---

### Stage C — VLM Attribute Extraction & Text Reading

**Goal:** infer structured watch attributes:
* `brand_guess`
* `dial_color`
* `bracelet_material`
* `confidence` and `short_explanation`

**Model family:** Qwen vision-language model (vision + text in chat format).

**Implementation: `apps/ai/vlm.py`**

**Primary model**
* Qwen 3.5 Vision 2B: `Qwen/Qwen3.5-2B`

**Backend strategy**
* Preferred: **unsloth** `FastVisionModel` path (fast on GPU)
* Fallback: Hugging Face transformers generation + processor

**Tasks**
1. **Text reading**  
   For each text crop, ask VLM to output only the visible text (OCR-like).
2. **Structured attribute extraction**  
   For the watch crop, ask VLM to output **JSON only** with fixed keys.

**Robust parsing**
* VLM responses may include chat prefixes and multiple JSON-looking blocks.
* Parsing logic strips prefixes and prefers the **last valid JSON object** in the response.

**Heuristic enrichment**
* If VLM returns missing/`null` brand, the router can infer a brand from detected text context (e.g. extracting `CASIO` from `WR50M CASIO JAPAN MOV`).

---

## 6. Technologies Used

### 6.1 Backend
* **FastAPI** (routing + request handling)
* **Pydantic** models for response schemas
* **SQLAlchemy** for DB connectivity
* **Supabase client** for vector and watch listing operations
* **PyTorch** + **transformers** for detection/embedding/VLM
* **Pillow / NumPy** for image and embedding handling

### 6.2 Frontend
* **Next.js** (React)
* **React Query** (`@tanstack/react-query`) for mutation management
* UI rendered in a split layout:
  * annotated image/crops
  * “Detected by AI” attributes and text

---

## 7. Debugging / Observability

Every `/ai/identify` call creates a per-request directory:

* `apps/api/static/debug/<request_id>/`
  * `original.jpg`
  * `annotated.jpg` (if detections exist)
  * `crop_watch.jpg`
  * `crop_<label>_<idx>.jpg` (text crops)
  * `debug.json`

`debug.json` includes:
* detection details (boxes, crops count, timing)
* embedding time and retrieval outcome
* VLM timing
* detected text map
* VLM parsed attributes

---

## 8. Model & Checkpoint Summary (v1)

* **Detector**
  * `rziga/mm_grounding_dino_tiny_o365v1_goldg` (default)
  * `iSEE-Laboratory/llmdet_tiny` (alternate)
* **Embedder**
  * `openai/clip-vit-base-patch16` (CLIP)
* **VLM**
  * `Qwen/Qwen3.5-2B` (primary)
  * Loader: unsloth `FastVisionModel` when available; else transformers fallback

---

## 9. Known Limitations (v1)

1. **CPU runtime for VLM**
   * Qwen 2B can be very slow on CPU.
   * unsloth typically expects GPU; if GPU is not available, transformers fallback is slower.

2. **Detector initialization quality**
   * Some model decoder heads can be initialized with missing checkpoint keys.
   * This is not necessarily fatal but can impact detection quality.

3. **Fragile text/JSON parsing**
   * VLM chat outputs can contain extra tokens outside JSON.
   * The system uses defensive parsing, but occasional edge cases can still occur.

4. **Embedding model compatibility**
   * If embeddings were generated with a different model than the one used during retrieval, similarity quality can degrade.

---

## 10. Next Moves (v2 roadmap)

These are planned improvements after the v1 identification milestone.

1. **GPU-first VLM deployment** (reduce latency; improve reliability)
2. **Constrained structured output**
   * stronger JSON-only generation guarantees or schema-based decoding
3. **Model contract consistency**
   * unify embedding model naming (`model_name` fields) and enforce re-embedding when models change
4. **Offline evaluation**
   * build a labeled test set and track metrics:
     * top-1 / top-5 retrieval accuracy
     * unknown rate
     * attribute extraction success rate
5. **Caching**
   * cache VLM results + embeddings per image hash to avoid recomputation
6. **UX improvements**
   * show “raw VLM JSON” in debug UI for easier troubleshooting
7. **Add additional VLM prompts**
   * separate prompts for brand/dial/bracelet to reduce JSON contamination

