"""Check Supabase connection and get project info."""
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

try:
    from supabase import create_client
    from sqlalchemy import create_engine, text
    
    # Get from environment or use defaults
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zedflowipppmlkspxkik.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InplZGZsb3dpcHBwbWxrc3B4a2lrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzMjMxNzAsImV4cCI6MjA4Mzg5OTE3MH0.nw9PqbkGZTqWJOecrShK8aPBqOgiJq6q6WhulOC7XVY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    print("🔍 Checking Supabase Connection")
    print("=" * 40)
    print(f"Project URL: {SUPABASE_URL}")
    print(f"API Key: {SUPABASE_KEY[:20]}...")
    print()
    
    # Test Supabase client
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client created successfully")
    except Exception as e:
        print(f"❌ Supabase client error: {e}")
    
    # Test database connection
    if DATABASE_URL:
        print(f"\n🔍 Testing database connection...")
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Database connected!")
                print(f"   PostgreSQL version: {version[:50]}...")
                
                # Check for pgvector
                try:
                    result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
                    if result.fetchone():
                        print("✅ pgvector extension enabled")
                    else:
                        print("⚠️  pgvector extension not found (will be enabled in migrations)")
                except:
                    print("⚠️  Could not check pgvector extension")
                
                # Check existing tables
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'watch_%'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result]
                if tables:
                    print(f"\n📊 Found {len(tables)} watch tables:")
                    for table in tables:
                        print(f"   - {table}")
                else:
                    print("\n📊 No watch tables found (run migrations first)")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    else:
        print("\n⚠️  DATABASE_URL not set")
        print("   Set it with: export DATABASE_URL='postgresql://postgres:PASSWORD@db.zedflowipppmlkspxkik.supabase.co:5432/postgres'")
    
    print("\n" + "=" * 40)
    
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Install with: cd apps/api && pip install -r requirements.txt")
    sys.exit(1)
