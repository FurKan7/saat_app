#!/bin/bash
# Quick setup with Supabase connection string

echo "🚀 Quick Supabase Setup"
echo "======================="
echo ""

# Get password
read -p "Enter your Supabase database password: " -s PASSWORD
echo ""

# Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:${PASSWORD}@db.zedflowipppmlkspxkik.supabase.co:5432/postgres"

echo ""
echo "✅ DATABASE_URL set!"
echo ""
echo "Testing connection..."

# Test connection
cd "$(dirname "$0")"
python3 -c "
import os
from sqlalchemy import create_engine, text

try:
    engine = create_engine(os.getenv('DATABASE_URL'), pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful!')
    print('')
    print('Next steps:')
    print('  1. Run: npm run migrate')
    print('  2. Run: npm run seed')
    print('  3. Run: npm run dev')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('')
    print('Please check your password and try again.')
" 2>/dev/null

echo ""
echo "💡 To make this permanent, add to your shell profile:"
echo "   export DATABASE_URL=\"postgresql://postgres:${PASSWORD}@db.zedflowipppmlkspxkik.supabase.co:5432/postgres\""
echo ""
echo "Or create .env file in apps/api/ with:"
echo "   DATABASE_URL=postgresql://postgres:${PASSWORD}@db.zedflowipppmlkspxkik.supabase.co:5432/postgres"
