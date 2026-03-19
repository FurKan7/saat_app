# AGENT PROMPT — Dual-Stage Watch ID: SigLIP2 Retrieval + VLM Attributes/Verification (CPU-Friendly)

## ROLE
You are an expert ML systems engineer + backend engineer + product engineer. Implement a robust dual-stage watch identification pipeline:

1) **Retrieval stage (fast, robust):** use **SigLIP2** to embed images and find the closest watch candidates in our DB using **pgvector** similarity search.  
2) **VLM stage (semantic extraction):** use **Qwen3-VL** or **SmolVLM2** to extract structured attributes (brand, dial_color, bracelet_material) and optionally verify the top candidate match.

We already have a working platform with:
- Supabase Postgres + pgvector
- Tables: `watch_core`, `watch_embeddings`, `watch_spec_state`, `watch_spec_sources`
- Image preservation script exists
- Resolver exists

Your job: implement AI services and DB integration for this dual-stage pipeline.

---

## HARD CONSTRAINTS
- Inference must complete ≤ 10 seconds per request (CPU-first).
- Retrieval must work even if VLM fails.
- VLM output must be strict JSON.
- No scraping during inference.

---

## PIPELINE

### Stage A — Detection / Cropping
Use watch-region cropping (GroundingDINO if available, else center crop).

### Stage B — SigLIP2 Retrieval
- Embed images
- Store vectors in pgvector
- Similarity search (top_k)

### Stage C — VLM Attribute Extraction
Return JSON only:
```json
{
  "brand_guess": "string|null",
  "dial_color": "string|null",
  "bracelet_material": "string|null",
  "confidence": 0.0,
  "short_explanation": "string"
}
```

### Stage D — Candidate Verification (Optional)
Compare query image vs candidate image.

### Stage E — Deterministic Decision Rules
Retrieval dominates; VLM never overrides DB match.

---

## MODELS
- Retrieval: SigLIP2
- VLM: SmolVLM2 (CPU), Qwen3-VL (GPU optional)

---

## API ENDPOINTS
- POST /ai/embed_watch_images
- POST /ai/identify

---

## UNKNOWN WATCH FLOW
If similarity is weak, ask user to add watch.

---

## DELIVERABLES
- AI service code
- DB migrations
- Retrieval + VLM integration
- Tests

---

## ACCEPTANCE TESTS
- Embedding job runs
- Identification <10s
- Retrieval works without VLM
- Unknown flow triggers
