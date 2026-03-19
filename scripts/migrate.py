"""Database migration script using Python (no psql required)."""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Get project root (handle both direct execution and via npm)
script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent

# Also try current working directory as fallback
cwd_root = Path.cwd()
if (cwd_root / "apps" / "api" / ".env").exists():
    project_root = cwd_root

# Load .env files in order of priority
# 1. Root .env
env_file_root = project_root / ".env"
try:
    if env_file_root.exists() and os.access(env_file_root, os.R_OK):
        load_dotenv(env_file_root, override=False)
except (PermissionError, OSError):
    pass  # Skip if we can't read it

# 2. apps/api/.env (override root) - this is the most important one
env_file_api = project_root / "apps" / "api" / ".env"
try:
    if env_file_api.exists() and os.access(env_file_api, os.R_OK):
        result = load_dotenv(env_file_api, override=True)
        if result:
            print(f"✅ Loaded .env from: {env_file_api}")
except (PermissionError, OSError):
    pass  # Skip if we can't read it

# 3. Environment variable (highest priority)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    print("")
    print("Checked locations:")
    print(f"  - Environment variable: {'set' if os.getenv('DATABASE_URL') else 'not set'}")
    print(f"  - {env_file_root}: {'exists' if env_file_root.exists() else 'not found'}")
    print(f"  - {env_file_api}: {'exists' if env_file_api.exists() else 'not found'}")
    print(f"  - Project root: {project_root}")
    print("")
    print("Set it with one of these methods:")
    print("  1. Export: export DATABASE_URL='postgresql://postgres:PASSWORD@db.zedflowipppmlkspxkik.supabase.co:5432/postgres'")
    print("  2. Create apps/api/.env file with DATABASE_URL=...")
    print("  3. Create .env file in project root with DATABASE_URL=...")
    print("  4. Run: npm run setup:supabase")
    print("")
    sys.exit(1)

# Show which DATABASE_URL is being used (mask password)
if DATABASE_URL:
    if '@' in DATABASE_URL:
        parts = DATABASE_URL.split('@')
        user_pass = parts[0].rsplit(':', 1)[0] + ":***"
        masked_url = user_pass + "@" + parts[1]
    else:
        masked_url = DATABASE_URL[:50] + "..." if len(DATABASE_URL) > 50 else DATABASE_URL
    print(f"📊 Using DATABASE_URL: {masked_url}")
    print("")


def run_migration_file(engine, migration_file: Path):
    """Run a SQL migration file."""
    if not migration_file.exists():
        print(f"⚠️  Migration file not found: {migration_file}")
        return False
    
    print(f"📄 Running {migration_file.name}...")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute SQL in a transaction
        # Use begin() for automatic commit/rollback
        with engine.begin() as conn:
            # Execute the entire file as one transaction
            # PostgreSQL can handle multiple statements separated by semicolons
            conn.execute(text(sql_content))
        
        print(f"✅ {migration_file.name} completed successfully")
        return True
    except Exception as e:
        # Some errors are expected (like extension already exists, or table already exists)
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["already exists", "duplicate", "relation already exists"]):
            print(f"⚠️  {migration_file.name} - Some objects may already exist (this is OK)")
            return True
        # For other errors, show the full error
        print(f"❌ Error running {migration_file.name}: {e}")
        # Don't return False immediately - try to continue with other migrations
        return False


def main():
    """Run all migrations."""
    migrations_dir = project_root / "migrations"
    
    if not migrations_dir.exists():
        print(f"ERROR: Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Create engine
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   DATABASE_URL: {DATABASE_URL[:50]}...")
        sys.exit(1)
    
    # Run migrations in order
    migration_files = [
        migrations_dir / "001_initial_schema.sql",
        migrations_dir / "002_enable_pgvector.sql",
        migrations_dir / "003_update_embeddings_for_siglip2.sql",
    ]
    
    print(f"\n🗄️  Running database migrations...")
    print(f"   Database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'unknown'}\n")
    
    success_count = 0
    for migration_file in migration_files:
        if run_migration_file(engine, migration_file):
            success_count += 1
        print("")  # Empty line between migrations
    
    print(f"✅ Migrations complete: {success_count}/{len(migration_files)} successful")
    
    # Verify tables exist
    print("\n🔍 Verifying tables...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'watch_%'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            if tables:
                print(f"✅ Found {len(tables)} watch tables:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No watch tables found")
    except Exception as e:
        print(f"⚠️  Could not verify tables: {e}")


if __name__ == "__main__":
    main()
