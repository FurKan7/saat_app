"""Database connection — SQLAlchemy direct + Supabase REST API fallback."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

api_dir = Path(__file__).parent.parent
env_file = api_dir / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    root_env = api_dir.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=True)
    else:
        load_dotenv(override=False)

DATABASE_URL = os.getenv("DATABASE_URL", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

Base = declarative_base()

# ── SQLAlchemy (direct connection) ──────────────────────────────────

_engine = None
_SessionLocal = None
_db_available = False

if DATABASE_URL and "localhost" not in DATABASE_URL and "watchdb" not in DATABASE_URL:
    try:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        _db_available = True
        print(f"[DB] SQLAlchemy engine created")
    except Exception as e:
        print(f"[DB] SQLAlchemy engine failed: {e}")
else:
    print(f"[DB] No valid DATABASE_URL, skipping SQLAlchemy")

# ── Supabase REST client (fallback) ────────────────────────────────

_supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[DB] Supabase REST client created")
    except ImportError:
        print("[DB] supabase-py not installed, REST fallback disabled. Install with: pip install supabase")
    except Exception as e:
        print(f"[DB] Supabase client failed: {e}")


def get_db():
    """SQLAlchemy session dependency. Yields None if unavailable."""
    if _SessionLocal is None:
        yield None
        return
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_supabase():
    """Return Supabase REST client or None."""
    return _supabase


def get_db_or_rest():
    """
    Dependency: returns (db_session_or_None, supabase_client_or_None).
    Prefers Supabase REST when configured (avoids flaky direct Postgres connection).
    """
    db = None
    # Prefer Supabase REST when available so we don't depend on direct DB connection
    if _supabase is not None:
        try:
            yield (None, _supabase)
            return
        finally:
            pass

    if _SessionLocal is not None:
        db = _SessionLocal()
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        except Exception as e:
            print(f"[DB] SQLAlchemy connection test failed: {e}")
            try:
                db.close()
            except Exception:
                pass
            db = None

    try:
        yield (db, _supabase)
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
