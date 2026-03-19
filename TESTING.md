# Testing Guide - Watch Community Platform

This guide covers how to test the application locally and verify all features.

## Prerequisites

1. **Node.js 20+** installed
2. **Python 3.11+** installed
3. **PostgreSQL** with pgvector extension (or Supabase account)
4. **Git** (if cloning from repository)

## Quick Start Testing

### 1. Install Dependencies

```bash
# Install all dependencies
npm install

# Install Python dependencies for backend
cd apps/api
pip install -r requirements.txt

# Install Python dependencies for AI service (optional, for full AI features)
cd ../ai
pip install -r requirements.txt
```

### 2. Set Up Database

#### Option A: Local PostgreSQL

```bash
# Install PostgreSQL and pgvector
# On macOS: brew install postgresql postgis
# On Ubuntu: sudo apt-get install postgresql postgresql-contrib

# Create database
createdb watchdb

# Set environment variable
export DATABASE_URL="postgresql://your_user:your_password@localhost:5432/watchdb"
```

#### Option B: Supabase (Recommended for Testing)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to Settings > Database and copy the connection string
4. Set environment variable:
   ```bash
   export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
   ```

### 3. Run Database Migrations

```bash
# Run migrations (Python-based, no psql required)
npm run migrate

# Or manually:
cd scripts && python migrate.py

# Alternative: If you have psql installed:
# psql $DATABASE_URL -f migrations/001_initial_schema.sql
# psql $DATABASE_URL -f migrations/002_enable_pgvector.sql
# psql $DATABASE_URL -f migrations/003_update_embeddings_for_siglip2.sql
```

### 4. Seed Database

```bash
# Seed with CSV data
npm run seed

# This will:
# - Load watches from watch_core_phase1_abtsaat.csv
# - Create watch_core records
# - Create initial watch_spec_state records
# - Create watch_spec_sources records
```

### 5. Start Development Servers

```bash
# Terminal 1: Start backend API
cd apps/api
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd apps/web
npm run dev

# Or use the root command (runs both):
npm run dev
```

The app should now be running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Testing Checklist

### ✅ Database & Data

- [ ] **Migrations run successfully**
  ```bash
  psql $DATABASE_URL -c "SELECT COUNT(*) FROM watch_core;"
  # Should return a number > 0
  ```

- [ ] **Seed data loaded**
  ```bash
  psql $DATABASE_URL -c "SELECT COUNT(*) FROM watch_core;"
  # Should show ~550+ watches
  ```

- [ ] **Spec states created**
  ```bash
  psql $DATABASE_URL -c "SELECT COUNT(*) FROM watch_spec_state;"
  # Should show multiple spec states
  ```

### ✅ Backend API Testing

#### Test Health Endpoint

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

#### Test Watch List

```bash
# Get all watches
curl http://localhost:8000/watches?limit=5

# Search watches
curl "http://localhost:8000/watches?query=Seiko&limit=5"

# Filter by brand
curl "http://localhost:8000/watches?brand=Citizen&limit=5"
```

#### Test Watch Detail

```bash
# Get watch detail (replace 1 with actual watch_id)
curl http://localhost:8000/watches/1

# Get watch specs
curl http://localhost:8000/watches/1/specs

# Get watch comments
curl http://localhost:8000/watches/1/comments
```

#### Test AI Identification (Without VLM)

```bash
# Test with image URL
curl -X POST http://localhost:8000/ai/identify \
  -F "image_url=https://example.com/watch.jpg" \
  -F "top_k=5" \
  -F "use_vlm=false"

# Test with image file
curl -X POST http://localhost:8000/ai/identify \
  -F "image_file=@/path/to/watch/image.jpg" \
  -F "top_k=5" \
  -F "use_vlm=false"
```

**Expected Response:**
```json
{
  "candidates": [
    {
      "watch_id": 1,
      "brand": "Seiko",
      "product_name": "...",
      "image_url": "...",
      "similarity_score": 0.85
    }
  ],
  "is_unknown": false,
  "retrieval_time_ms": 1500
}
```

### ✅ Frontend Testing

#### 1. Home Page
- Navigate to http://localhost:3000
- [ ] Page loads without errors
- [ ] Search bar is visible
- [ ] Brand filter dropdown works
- [ ] Watch cards display with images
- [ ] Clicking a watch navigates to detail page

#### 2. Watch List Page
- Navigate to http://localhost:3000/watches
- [ ] All watches display
- [ ] Pagination works
- [ ] Search filters results
- [ ] Brand filter works

#### 3. Watch Detail Page
- Navigate to http://localhost:3000/watches/1
- [ ] Watch image displays
- [ ] Watch name and brand show
- [ ] Specs display with badges (Official/Verified/AI/Unknown/Disputed)
- [ ] "Contribute" button appears for unknown specs
- [ ] Comments section visible
- [ ] Contributions section visible

#### 4. Upload/Identify Page
- Navigate to http://localhost:3000/upload
- [ ] Upload form displays
- [ ] Can upload image file
- [ ] Can enter image URL
- [ ] Preview shows uploaded image
- [ ] After identification:
  - [ ] Candidates display
  - [ ] Similarity scores show
  - [ ] Can click to navigate to watch detail
  - [ ] VLM attributes display (if VLM enabled)
  - [ ] Unknown watch flow triggers if similarity < 0.5

### ✅ Feature Testing

#### Test Comments (Requires Auth)

1. **Set up Supabase Auth** (or mock auth for testing):
   - Create Supabase project
   - Get auth token
   - Add to request headers: `Authorization: Bearer <token>`

2. **Create Comment:**
   ```bash
   curl -X POST http://localhost:8000/watches/1/comments \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"content": "Great watch!", "rating": 5}'
   ```

3. **Verify in Frontend:**
   - Go to watch detail page
   - Comment should appear in comments list

#### Test Contributions (Requires Auth)

1. **Create Contribution:**
   ```bash
   curl -X POST http://localhost:8000/watches/1/contributions \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "spec_key": "weight_g",
       "proposed_value": "150",
       "unit": "g",
       "note": "Measured with scale",
       "evidence_url": "https://example.com/evidence.jpg"
     }'
   ```

2. **Vote on Contribution:**
   ```bash
   curl -X POST http://localhost:8000/contributions/1/vote \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"vote_type": "confirm"}'
   ```

3. **Test Resolver:**
   ```bash
   # After 3+ confirms, run resolver
   curl -X POST "http://localhost:8000/resolver/run?watch_id=1"
   ```

4. **Verify:**
   - Contribution appears on watch detail page
   - Votes display correctly
   - After 3 confirms, spec state updates to "community_verified"

#### Test Resolver Logic

1. **Check Spec State:**
   ```bash
   curl http://localhost:8000/watches/1/specs
   ```

2. **Verify Priority:**
   - Official specs should show `source_type: "official"`
   - After community verification: `source_type: "community_verified"`
   - Disputed specs: `source_type: "disputed"`

### ✅ AI/VLM Testing

#### Test Embedding Generation

```bash
# Embed all watches (text-based)
curl -X POST http://localhost:8000/ai/embed_watch_core

# Embed watch images (requires images to be downloaded)
curl -X POST http://localhost:8000/ai/embed_watch_images
```

#### Test Dual-Stage Identification

1. **With VLM (Full Pipeline):**
   ```bash
   curl -X POST http://localhost:8000/ai/identify \
     -F "image_file=@test_watch.jpg" \
     -F "top_k=5" \
     -F "use_vlm=true"
   ```

2. **Without VLM (Retrieval Only):**
   ```bash
   curl -X POST http://localhost:8000/ai/identify \
     -F "image_file=@test_watch.jpg" \
     -F "top_k=5" \
     -F "use_vlm=false"
   ```

3. **Verify Response:**
   - Retrieval always works (even if VLM fails)
   - VLM attributes included when `use_vlm=true`
   - Timing metrics included
   - Unknown watch flag set if similarity < 0.5

### ✅ Performance Testing

#### Test Response Times

```bash
# Time the identification endpoint
time curl -X POST http://localhost:8000/ai/identify \
  -F "image_file=@test_watch.jpg" \
  -F "top_k=5" \
  -F "use_vlm=false"

# Should complete in < 10 seconds (CPU constraint)
```

#### Test Database Queries

```bash
# Test watch list performance
time curl "http://localhost:8000/watches?limit=100"

# Test search performance
time curl "http://localhost:8000/watches?query=Seiko&limit=50"
```

### ✅ Acceptance Criteria Testing

#### MVP Success Checks

1. **Dataset loads:**
   ```bash
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM watch_core;"
   # Should return 550+
   ```

2. **Watch list shows:**
   - Navigate to http://localhost:3000/watches
   - Verify watches display with pagination

3. **Watch detail shows specs with badges:**
   - Navigate to any watch detail page
   - Verify spec badges display (Official/Verified/AI/Unknown/Disputed)

4. **Can add comment:**
   - Requires authentication
   - Test via API or frontend (if auth configured)

5. **Can propose contribution:**
   - Create contribution via API
   - Verify it appears on watch detail page

6. **Can vote on contribution:**
   - Vote confirm/reject
   - Verify vote counts update

7. **Resolver updates state:**
   - After 3+ confirms, run resolver
   - Verify spec state changes to "community_verified"

8. **Upload image returns candidates:**
   - Upload image via frontend
   - Verify candidates display with similarity scores

9. **Unknown watch flow:**
   - Upload image with low similarity (< 0.5)
   - Verify "Unknown Watch" message appears
   - Verify "Add New Watch" button appears

## Automated Testing

### API Testing with pytest (Optional)

Create `apps/api/tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_watch_list():
    response = client.get("/watches?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "watches" in data
    assert len(data["watches"]) <= 5

def test_watch_detail():
    response = client.get("/watches/1")
    assert response.status_code == 200
    data = response.json()
    assert "watch_id" in data
    assert data["watch_id"] == 1
```

Run tests:
```bash
cd apps/api
pytest tests/
```

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT version();"

# Check pgvector extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Backend Not Starting

```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
cd apps/api
pip list | grep fastapi

# Check for port conflicts
lsof -i :8000
```

### Frontend Not Starting

```bash
# Check Node version
node --version  # Should be 20+

# Clear cache and reinstall
cd apps/web
rm -rf node_modules .next
npm install
npm run dev
```

### AI Features Not Working

```bash
# Check if transformers installed
cd apps/ai
python -c "import transformers; print(transformers.__version__)"

# Test model loading
python -c "from embedder import get_model; get_model()"
```

## Next Steps

After basic testing passes:

1. **Set up Supabase Auth** for full feature testing
2. **Download watch images** using `npm run download-images`
3. **Generate embeddings** using `/ai/embed_watch_images`
4. **Test end-to-end flow** with real watch images
5. **Deploy to staging** environment for integration testing

## Test Data

Sample test images can be found in:
- `watch_images/` (after running download script)
- Or use any watch image URL from the dataset

Sample watch IDs for testing:
- Watch ID 1: Seiko Prospex SPB103J
- Watch ID 3: Citizen Promaster BN2040-17X
- Check `watch_core_phase1_abtsaat.csv` for more
