#!/bin/bash
# Database setup helper script

echo "🗄️  Database Setup Helper"
echo "========================"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL is not set."
    echo ""
    echo "Choose an option:"
    echo ""
    echo "1. Use Supabase (Recommended - Free, no local setup needed)"
    echo "2. Use Local PostgreSQL (Requires PostgreSQL installed)"
    echo "3. Skip for now (set DATABASE_URL manually later)"
    echo ""
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            echo ""
            echo "📝 Supabase Setup:"
            echo "1. Go to https://supabase.com and create a free account"
            echo "2. Create a new project"
            echo "3. Go to Settings > Database"
            echo "4. Copy the connection string (Connection Pooling or Direct Connection)"
            echo ""
            echo "Example format:"
            echo "postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
            echo ""
            read -p "Paste your Supabase connection string: " db_url
            export DATABASE_URL="$db_url"
            echo ""
            echo "✅ DATABASE_URL set!"
            echo "   Run: export DATABASE_URL='$db_url'"
            echo "   Or add it to your .env file"
            ;;
        2)
            echo ""
            echo "📝 Local PostgreSQL Setup:"
            echo ""
            
            # Check if PostgreSQL is installed
            if ! command -v psql &> /dev/null; then
                echo "⚠️  PostgreSQL is not installed."
                echo ""
                echo "Install it:"
                echo "  macOS: brew install postgresql"
                echo "  Ubuntu: sudo apt-get install postgresql postgresql-contrib"
                echo "  Windows: Download from https://www.postgresql.org/download/"
                echo ""
                exit 1
            fi
            
            read -p "PostgreSQL username (default: postgres): " pg_user
            pg_user=${pg_user:-postgres}
            
            read -p "PostgreSQL password: " -s pg_pass
            echo ""
            
            read -p "Database name (default: watchdb): " db_name
            db_name=${db_name:-watchdb}
            
            read -p "Host (default: localhost): " pg_host
            pg_host=${pg_host:-localhost}
            
            read -p "Port (default: 5432): " pg_port
            pg_port=${pg_port:-5432}
            
            db_url="postgresql://${pg_user}:${pg_pass}@${pg_host}:${pg_port}/${db_name}"
            
            echo ""
            echo "Creating database if it doesn't exist..."
            PGPASSWORD="$pg_pass" psql -h "$pg_host" -p "$pg_port" -U "$pg_user" -d postgres -c "CREATE DATABASE $db_name;" 2>/dev/null || echo "Database may already exist"
            
            export DATABASE_URL="$db_url"
            echo ""
            echo "✅ DATABASE_URL set!"
            echo "   Run: export DATABASE_URL='$db_url'"
            echo "   Or add it to your .env file"
            ;;
        3)
            echo ""
            echo "⏭️  Skipping database setup."
            echo ""
            echo "To set DATABASE_URL later, run:"
            echo "  export DATABASE_URL='postgresql://user:password@host:port/dbname'"
            echo ""
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    echo "✅ DATABASE_URL is already set"
    echo "   Current: ${DATABASE_URL:0:50}..."
    echo ""
fi

# Test connection
if [ ! -z "$DATABASE_URL" ]; then
    echo "🔍 Testing database connection..."
    cd "$(dirname "$0")"
    python3 -c "
import os
import sys
from sqlalchemy import create_engine, text

try:
    engine = create_engine(os.getenv('DATABASE_URL'), pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ Database connection successful!')
    sys.exit(0)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Ready to run migrations!"
        echo "   Run: npm run migrate"
    else
        echo ""
        echo "⚠️  Connection test failed. Please check your DATABASE_URL"
    fi
fi
