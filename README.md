# Watch Community Platform

A production-grade watch community platform with AI/VLM support for watch identification, community contributions, and spec verification.

## Architecture

### Stack

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + TanStack Query
- **Backend**: FastAPI (Python) with SQLAlchemy
- **Database**: PostgreSQL with pgvector (Supabase)
- **AI/VLM**: SigLIP embeddings via transformers
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage
- **Hosting**: 
  - Frontend: Netlify
  - Backend: Railway
  - Database: Supabase

### Data Model

The platform uses a multi-layer data model to support incomplete official data and community contributions:

1. **watch_core**: Immutable seed data from CSV
2. **watch_spec_state**: Current "best known" resolved value per spec
3. **watch_spec_sources**: Traceability of which source provided which value
4. **watch_user_contributions**: User-proposed spec values with evidence
5. **watch_contribution_votes**: Community voting (confirm/reject)
6. **watch_ai_estimations**: AI-estimated values (never overwrites official)
7. **watch_embeddings**: Vector embeddings for similarity search

### Resolver Logic

The resolver determines the "best known" spec value based on priority:

1. **Official** - From `watch_spec_sources` with `source_type='official'`
2. **Community Verified** - Contribution with >=3 confirms and median value stable
3. **AI Estimated** - From `watch_ai_estimations` with `confidence >= 0.7`
4. **Unknown** - Default fallback

## Project Structure

```
/
├── apps/
│   ├── web/              # Next.js frontend
│   ├── api/              # FastAPI backend
│   └── ai/               # AI/VLM service (SigLIP)
├── packages/
│   └── shared/           # TypeScript types and Zod schemas
├── migrations/           # SQL migration files
├── scripts/
│   └── seed.py           # CSV ingestion script
└── README.md
```

## Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL with pgvector extension
- Supabase account (for auth and storage)

### Local Development

1. **Clone and install dependencies**:
   ```bash
   npm install
   ```

2. **Set up database connection**:
   
   **Option A: Use Supabase (Recommended - Free, Easy)**
   ```bash
   # Run interactive setup script
   ./scripts/setup_database.sh
   
   # Or manually:
   # 1. Go to https://supabase.com and create a project
   # 2. Get connection string from Settings > Database
   # 3. Set environment variable:
   export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
   ```
   
   **Option B: Local PostgreSQL**
   ```bash
   # Install PostgreSQL first, then:
   ./scripts/setup_database.sh
   ```

3. **Set up environment variables**:
   
   Create `apps/api/.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/watchdb
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   JWT_SECRET=your-secret-key
   ```

   Create `apps/web/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   # Optional: copy apps/web/.env.example → apps/web/.env.local for email login (same Supabase project as the API)
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   NEXT_PUBLIC_SITE_URL=http://localhost:3000
   ```

   **Password reset:** In Supabase → **Authentication** → **URL configuration**, add these to **Redirect URLs** (adjust host/port if needed):
   - `http://localhost:3000/auth/reset-password`
   - Your production site URL with the same path for deploys.

4. **Run database migrations**:
   ```bash
   # Run migrations (Python-based, no psql required)
   npm run migrate
   
   # Or manually:
   cd scripts && python migrate.py
   ```

4. **Seed database**:
   ```bash
   npm run seed
   ```

5. **Start development servers**:
   ```bash
   npm run dev
   ```
   
   This starts:
   - Backend API at http://localhost:8000
   - Frontend at http://localhost:3000

### Individual Services

- **Backend only**: `npm run dev:api`
- **Frontend only**: `npm run dev:web`

If you run uvicorn yourself, start it from **`apps/api`** (the FastAPI package is `app` there). From the repo root, `uvicorn app.main:app` fails because `app` would resolve to the root `app.py` (Gradio), not `apps/api/app/main.py`.

```bash
cd apps/api
conda activate saat_app   # or your venv
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Watches

- `GET /watches?query=&brand=&page=&limit=20` - List watches with search/filter
- `GET /watches/{watch_id}` - Get watch detail
- `GET /watches/{watch_id}/specs` - Get watch specs with sources
- `GET /watches/{watch_id}/comments` - Get comments
- `POST /watches/{watch_id}/comments` - Add comment (auth required)

### Contributions

- `POST /watches/{watch_id}/contributions` - Propose spec value (auth required)
- `GET /watches/{watch_id}/contributions` - List contributions
- `POST /contributions/{contribution_id}/vote` - Vote on contribution (auth required)

### Resolver

- `POST /resolver/run?watch_id=X` - Run resolver (admin)

### AI

- `POST /ai/identify` - Dual-stage identification (SigLIP2 retrieval + VLM attributes)
- `POST /ai/embed_watch_images` - Admin: embed watch images using SigLIP2
- `POST /ai/embed_watch_core` - Admin: embed watches using text payload (legacy)

## Deployment

### Database (Supabase)

1. Create a new Supabase project
2. Enable pgvector extension in SQL editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Run migrations:
   ```bash
   psql $DATABASE_URL -f migrations/001_initial_schema.sql
   psql $DATABASE_URL -f migrations/002_enable_pgvector.sql
   ```
4. Create storage bucket `watch-images` for evidence uploads
5. Get connection string and API keys from project settings

### Backend (Railway)

1. Create a new Railway project
2. Connect your GitHub repository
3. Set root directory to `apps/api`
4. Add environment variables:
   - `DATABASE_URL` (from Supabase)
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `JWT_SECRET`
5. Deploy (Railway will auto-detect Python and install dependencies)

**Alternative**: Use the provided `Dockerfile`:
```bash
docker build -t watch-api -f apps/api/Dockerfile .
docker run -p 8000:8000 --env-file apps/api/.env watch-api
```

### Frontend (Netlify)

1. Create a new Netlify site
2. Connect your GitHub repository
3. Set build settings:
   - **Build command**: `cd apps/web && npm install && npm run build`
   - **Publish directory**: `apps/web/.next`
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL` (your Railway backend URL)
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. Deploy

### Post-Deployment

1. **Seed the database**:
   ```bash
   DATABASE_URL=your-production-db-url npm run seed
   ```

2. **Embed watches for AI search**:
   ```bash
   # Call the admin endpoint
   curl -X POST https://your-api-url.com/ai/embed_watch_core
   ```

## Commands

- `npm install` - Install all dependencies
- `npm run dev` - Run frontend + backend in dev mode
- `npm run migrate` - Run database migrations
- `npm run seed` - Run CSV ingestion script
- `npm run build` - Build frontend
- `npm run deploy:api` - Deploy backend (instructions)
- `npm run deploy:web` - Deploy frontend (instructions)

## Acceptance Criteria

✅ **MVP Success Checks**:

1. ✅ Dataset loads: 550+ watches in `watch_core`
2. ✅ Watch list shows with pagination
3. ✅ Watch detail shows spec_state + badge
4. ✅ Can add comment (requires auth)
5. ✅ Can propose `weight_g` contribution
6. ✅ Can vote on contribution (confirm/reject)
7. ✅ Resolver updates state to `community_verified` after 3 confirms
8. ✅ Upload image returns top 5 candidate watches

## Development Notes

### AI/VLM Service

The AI service uses a dual-stage pipeline:

**Stage A: Detection/Cropping**
- Watch region cropping (center crop fallback, GroundingDINO optional)

**Stage B: SigLIP2 Retrieval** (always runs, must work even if VLM fails)
- Model: `google/siglip-so400m-patch14-384` (SigLIP2)
- Embeddings: Vector embeddings stored in pgvector
- Similarity search: HNSW index for fast retrieval
- CPU-friendly: Works on CPU-only environments

**Stage C: VLM Attribute Extraction** (optional)
- Model: `HuggingFaceTB/SmolVLM2-Instruct` (CPU-friendly)
- Extracts: brand_guess, dial_color, bracelet_material
- Returns: Strict JSON format
- Non-blocking: Retrieval works even if VLM fails

**Stage D: Candidate Verification** (optional)
- Compares query image vs candidate image
- Used for additional validation

**Stage E: Decision Rules**
- Retrieval dominates; VLM never overrides DB match
- Unknown watch flow triggers if similarity < 0.5

To use AI features, ensure transformers and torch are installed:
```bash
cd apps/ai
pip install -r requirements.txt
```

**Performance:**
- Inference completes ≤ 10 seconds per request (CPU-first)
- Retrieval typically < 2 seconds
- VLM extraction typically < 5 seconds

### Retrieval Evaluation and Threshold Tuning

The platform includes an evaluation pipeline to compute optimal similarity thresholds for watch identification.

#### Running Evaluation

```bash
# Install evaluation dependencies (if not already installed)
pip install pandas httpx

# Run evaluation (samples 50 watches by default)
# Make sure API is running: npm run dev:api
python scripts/eval_retrieval.py

# Customize sample size and seed
python scripts/eval_retrieval.py --n 100 --seed 123

# Use custom API URL
python scripts/eval_retrieval.py --api-url http://localhost:8000

# Skip evaluation, only run grid search on existing data
python scripts/eval_retrieval.py --skip-eval
```

#### Output Files

The evaluation generates two CSV files in `reports/`:

1. **`retrieval_eval_raw.csv`**: Raw evaluation results with columns:
   - `watch_id`: The watch being queried
   - `expected_watch_id`: Ground truth watch ID
   - `top1_watch_id`, `top1_score`: Top candidate and its similarity score
   - `top2_watch_id`, `top2_score`: Second candidate and its similarity score
   - `gap`: Difference between top1 and top2 scores
   - `is_correct`: Whether top1 matches expected watch
   - `api_time_ms`: API response time

2. **`threshold_grid.csv`**: Grid search results with columns:
   - `sim_top1_min`: Minimum top-1 similarity threshold
   - `sim_gap_min`: Minimum gap threshold
   - `n_matched`: Number of queries that pass both thresholds
   - `n_correct`: Number of correct matches
   - `n_false_positive`: Number of false positives
   - `false_positive_rate`: False positive rate (target: ≤1%)
   - `coverage`: Percentage of queries matched
   - `accuracy_matched`: Accuracy among matched queries

#### Interpreting Results

The script automatically recommends optimal thresholds based on:
1. **Minimize false positive rate** (hard constraint: ≤1%)
2. **Maximize accuracy** among matched queries
3. **Maximize coverage** (percentage of queries matched)

The recommended thresholds are printed at the end:
```
🎯 RECOMMENDED THRESHOLDS
SIM_TOP1_MIN = 0.65
SIM_GAP_MIN = 0.03

Metrics at these thresholds:
  False Positive Rate: 0.50%
  Coverage: 85.0%
  Accuracy (matched): 98.5%
  Matched queries: 42/50
```

#### Recommended Default Thresholds

After running evaluation on your dataset, use the recommended values. Typical defaults:
- **SIM_TOP1_MIN**: 0.60-0.70 (higher = stricter, fewer false positives)
- **SIM_GAP_MIN**: 0.02-0.05 (higher = requires clearer top candidate)

These thresholds should be configured in your API code (e.g., `apps/api/app/routers/ai.py`) to filter retrieval results.

### Spec Key Normalization

The system normalizes spec keys from various formats (Turkish, English variations) to canonical keys. See `packages/shared/src/schemas.ts` for the mapping.

### Authentication

Currently uses Supabase Auth. Users are automatically created in the `users` table on first API call with a valid Supabase JWT token.

## Testing

See [TESTING.md](TESTING.md) for comprehensive testing instructions including:
- Local setup and running
- Database setup
- API testing with curl
- Frontend testing
- Feature testing (comments, contributions, voting)
- AI/VLM testing
- Performance testing
- Acceptance criteria verification

Quick test:
```bash
# Start servers
npm run dev

# In another terminal, test API
curl http://localhost:8000/health
curl http://localhost:8000/watches?limit=5
```

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` format: `postgresql://user:password@host:port/dbname`
- Check pgvector extension is enabled: `SELECT * FROM pg_extension WHERE extname = 'vector';`

### AI Service Not Working

- Check if transformers and torch are installed
- Verify model downloads correctly (first run downloads ~500MB)
- Check GPU availability for faster inference (optional)

### Frontend Build Errors

- Ensure `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS settings in backend if API calls fail
- Verify Supabase keys are correct

## License

MIT

## Contributing

This is a production MVP. For production use, consider:
- Adding rate limiting
- Implementing proper admin authentication
- Adding image upload to Supabase Storage
- Optimizing AI model loading (caching, quantization)
- Adding comprehensive error handling and logging
- Setting up CI/CD pipelines

