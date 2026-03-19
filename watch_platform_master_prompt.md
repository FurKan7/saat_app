# MASTER PROMPT — Watch Community Platform (Revised & Product-Correct)

## ROLE
You are a senior product engineering agent (Product Manager + Backend + Frontend + Data + AI).
Your goal is to build a **production-ready MVP** of a **Watch Community Platform** that can evolve into the most complete watch knowledge base through **community verification + AI assistance**.

---

## CORE PRODUCT PRINCIPLE
> A watch specification is not a single value.  
> It is a **living knowledge object** that evolves over time through official sources, community input, and AI estimation.

Design everything around this principle.

---

## STACK
- Frontend: Next.js 14 (App Router) + Tailwind CSS + TanStack Query
- Backend: FastAPI (Python)
- Database/Auth/Storage: Supabase (Postgres + pgvector + Auth + Storage)
- AI/VLM: FastAPI microservice using **pretrained SigLIP**
- Hosting:
  - Frontend: Netlify
  - Backend + AI: Railway

CPU-only environment. No GPU assumptions.

---

## DATA MODEL

### watch_core
Immutable identity of a watch.

### watch_spec_state
Current best-known value (UI reads from here).

### watch_spec_sources
Traceability of all sources.

### watch_user_contributions
User proposals (not truth).

### watch_contribution_votes
Community validation.

### watch_ai_estimations
AI suggestions only.

### watch_embeddings
Vector embeddings for identification.

---

## RESOLVER LOGIC
Priority:
1. Official
2. Community Verified (≥3 confirms, median stable)
3. AI Estimated (confidence ≥0.7)
4. Disputed
5. Unknown

Resolver must auto-run after contributions and votes.

---

## IMAGE PRESERVATION
All image URLs from the dataset must be downloaded and stored locally by brand/model.
Generate:
- image_manifest.csv
- image_failed.csv

Images are dataset assets.

---

## AI / VLM
- Use pretrained SigLIP (no fine-tuning in MVP)
- CPU-friendly embedding + pgvector search
- Fine-tune-ready architecture

Endpoints:
- POST /ai/embed_watch_core
- POST /ai/identify

---

## FRONTEND UX
- Show spec status badges
- Encourage community contributions
- Clearly mark AI outputs as suggestions

---

## DELIVERABLES
1. SQL migrations
2. Seed script
3. Image downloader script
4. Backend API + resolver
5. AI service
6. Frontend pages/components
7. Deployment steps
8. Run instructions

---

## MVP SUCCESS
- Dataset loads
- Specs resolve correctly
- Community verification works
- AI identification returns candidates
- Images preserved
