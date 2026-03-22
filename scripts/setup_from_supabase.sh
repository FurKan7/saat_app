#!/bin/bash
# Auto-setup environment from Supabase MCP (if available)
# Falls back to manual setup if MCP not available

echo "🔧 Auto-Setting Up Environment from Supabase"
echo "============================================"
echo ""

# Get database password from user
read -p "Enter your Supabase database password: " -s SUPABASE_PASSWORD
echo ""

# Supabase project details (from MCP or hardcoded)
SUPABASE_PROJECT_REF="zedflowipppmlkspxkik"
SUPABASE_URL="https://${SUPABASE_PROJECT_REF}.supabase.co"
SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InplZGZsb3dpcHBwbWxrc3B4a2lrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzMjMxNzAsImV4cCI6MjA4Mzg5OTE3MH0.nw9PqbkGZTqWJOecrShK8aPBqOgiJq6q6WhulOC7XVY"

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change-this-secret-key-in-production")

# Database URL
DATABASE_URL="postgresql://postgres:${SUPABASE_PASSWORD}@db.${SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"

echo "📝 Creating environment files..."
echo ""

# Backend .env
mkdir -p apps/api
cat > apps/api/.env << EOF
# Supabase Database
DATABASE_URL=${DATABASE_URL}

# Supabase API
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_KEY=${SUPABASE_ANON_KEY}

# JWT Secret (auto-generated)
JWT_SECRET=${JWT_SECRET}
EOF

echo "✅ Created apps/api/.env"

# Frontend .env.local
mkdir -p apps/web
cat > apps/web/.env.local << EOF
# API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase (for auth) — use the same JWT anon key as SUPABASE_KEY (eyJ...), not sb_publishable_*
NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
EOF

echo "✅ Created apps/web/.env.local"

# Root .env (for scripts)
cat > .env << EOF
# Supabase Database
DATABASE_URL=${DATABASE_URL}

# Supabase API
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_KEY=${SUPABASE_ANON_KEY}

# JWT Secret
JWT_SECRET=${JWT_SECRET}
EOF

echo "✅ Created .env"
echo ""

# Test database connection
echo "🔍 Testing database connection..."
cd "$(dirname "$0")"
python3 -c "
import os
import sys
from sqlalchemy import create_engine, text

try:
    engine = create_engine('${DATABASE_URL}', pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful!')
    sys.exit(0)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('   Please check your password')
    sys.exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Run migrations: npm run migrate"
    echo "  2. Seed data: npm run seed"
    echo "  3. Start app: npm run dev"
    echo ""
else
    echo ""
    echo "⚠️  Connection test failed. Please verify your password."
    echo "   You can still try running migrations manually."
fi
