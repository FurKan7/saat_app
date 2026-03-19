#!/bin/bash
# Quick environment setup script

echo "🔧 Setting up environment variables"
echo "===================================="
echo ""

# Get Supabase password
read -p "Enter your Supabase database password: " -s SUPABASE_PASSWORD
echo ""

# Get Supabase API key (optional but recommended)
read -p "Enter your Supabase anon key (or press Enter to skip): " SUPABASE_KEY

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change-this-secret-key-in-production")

# Create .env files
echo ""
echo "📝 Creating environment files..."

# Backend .env
cat > apps/api/.env << EOF
DATABASE_URL=postgresql://postgres:${SUPABASE_PASSWORD}@db.zedflowipppmlkspxkik.supabase.co:5432/postgres
SUPABASE_URL=https://zedflowipppmlkspxkik.supabase.co
SUPABASE_KEY=${SUPABASE_KEY:-your-supabase-anon-key}
JWT_SECRET=${JWT_SECRET}
EOF

# Frontend .env.local
cat > apps/web/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://zedflowipppmlkspxkik.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_KEY:-your-supabase-anon-key}
EOF

# Root .env (for scripts)
cat > .env << EOF
DATABASE_URL=postgresql://postgres:${SUPABASE_PASSWORD}@db.zedflowipppmlkspxkik.supabase.co:5432/postgres
SUPABASE_URL=https://zedflowipppmlkspxkik.supabase.co
SUPABASE_KEY=${SUPABASE_KEY:-your-supabase-anon-key}
JWT_SECRET=${JWT_SECRET}
EOF

echo "✅ Environment files created!"
echo ""
echo "Files created:"
echo "  - apps/api/.env"
echo "  - apps/web/.env.local"
echo "  - .env"
echo ""
echo "⚠️  Note: Add these files to .gitignore (already included)"
echo ""
echo "Next steps:"
echo "  1. Get your Supabase anon key from: https://supabase.com/dashboard/project/zedflowipppmlkspxkik/settings/api"
echo "  2. Update SUPABASE_KEY in the .env files if you skipped it"
echo "  3. Run: npm run migrate"
echo "  4. Run: npm run seed"
echo "  5. Run: npm run dev"
echo ""
