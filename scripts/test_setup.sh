#!/bin/bash
# Quick test setup script for Watch Community Platform

set -e

echo "🧪 Watch Community Platform - Test Setup"
echo "=========================================="

# Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 20+"
    exit 1
fi
echo "✅ Node.js $(node --version)"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi
echo "✅ Python $(python3 --version)"

if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. You'll need it for database setup."
else
    echo "✅ PostgreSQL client found"
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo ""
    echo "⚠️  DATABASE_URL not set"
    echo "Please set it:"
    echo "  export DATABASE_URL='postgresql://user:password@localhost:5432/watchdb'"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ DATABASE_URL is set"
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

echo ""
echo "🐍 Installing Python dependencies..."
cd apps/api
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Run migrations if DATABASE_URL is set
if [ ! -z "$DATABASE_URL" ]; then
    echo ""
    echo "🗄️  Running database migrations..."
    psql $DATABASE_URL -f migrations/001_initial_schema.sql || echo "⚠️  Migration 001 failed (may already exist)"
    psql $DATABASE_URL -f migrations/002_enable_pgvector.sql || echo "⚠️  Migration 002 failed (may already exist)"
    psql $DATABASE_URL -f migrations/003_update_embeddings_for_siglip2.sql || echo "⚠️  Migration 003 failed (may already exist)"
    
    echo ""
    read -p "Run seed script to load data? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🌱 Seeding database..."
        npm run seed
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the app:"
echo "  npm run dev"
echo ""
echo "Or start separately:"
echo "  Terminal 1: cd apps/api && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Terminal 2: cd apps/web && npm run dev"
echo ""
echo "Then test:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/watches?limit=5"
echo "  Open http://localhost:3000 in browser"
echo ""
