# Quick Start Guide

Get the Watch Community Platform running in 5 minutes!

## Step 1: Install Dependencies

```bash
npm install
cd apps/api && pip install -r requirements.txt
```

## Step 2: Set Up Database (Choose One)

### Option A: Supabase (Recommended - No Local Setup)

1. Go to [supabase.com](https://supabase.com) and sign up (free)
2. Create a new project
3. Go to **Settings > Database**
4. Copy the **Connection string** (use "Connection pooling" or "Direct connection")
5. Set it as environment variable:

```bash
export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
```

**Or use the interactive setup:**
```bash
./scripts/setup_database.sh
```

### Option B: Local PostgreSQL

```bash
# Install PostgreSQL first, then:
./scripts/setup_database.sh
```

## Step 3: Run Migrations

```bash
npm run migrate
```

This will create all database tables.

## Step 4: Seed Data (Optional)

```bash
npm run seed
```

This loads watches from the CSV file.

## Step 5: Start the App

```bash
# Start both frontend and backend
npm run dev

# Or separately:
# Terminal 1: npm run dev:api
# Terminal 2: npm run dev:web
```

## Step 6: Test It!

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Quick API Test

```bash
curl http://localhost:8000/health
curl http://localhost:8000/watches?limit=5
```

## Troubleshooting

### Database Connection Error?

1. **Check DATABASE_URL is set:**
   ```bash
   echo $DATABASE_URL
   ```

2. **Test connection:**
   ```bash
   ./scripts/setup_database.sh
   ```

3. **For Supabase:** Make sure you copied the full connection string including password

### Watches not loading / “Could not load watches”?

The watch list comes from the API. You need **both** the API and the web app running:

1. **Terminal 1 – API:** `npm run dev:api` (or run both with `npm run dev`)
2. **Terminal 2 – Web:** `npm run dev:web`

Ensure `NEXT_PUBLIC_API_URL` in `apps/web/.env.local` matches your API (default `http://localhost:8000`). If the API is on another host/port, set it there.

### npm “ENOWORKSPACES” when running dev:web?

The root script runs `npx next dev` inside `apps/web` to avoid workspace issues. If you still see it, run the app from the web app directory:

```bash
cd apps/web && npm run dev
```

### Port Already in Use?

```bash
# Check what's using port 8000
lsof -i :8000

# Or use different ports:
# Backend: uvicorn app.main:app --reload --port 8001
# Frontend: Change NEXT_PUBLIC_API_URL in .env.local
```

### Python Dependencies Error?

```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Next Steps

- See [TESTING.md](TESTING.md) for comprehensive testing
- See [README.md](README.md) for full documentation
- Download watch images: `npm run download-images`
- Generate embeddings: `curl -X POST http://localhost:8000/ai/embed_watch_images`
