"""Seed script to ingest CSV data into database."""
import csv
import os
import sys
import time
from decimal import Decimal
from pathlib import Path

# Add parent directory to path to import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError
from dotenv import load_dotenv

# Import models
from app.models import (
    WatchCore,
    WatchSpecState,
    WatchSpecSource,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/watchdb")

# Required spec keys from schema
REQUIRED_SPEC_KEYS = [
    "case_diameter_mm",
    "gender",
    "water_resistance_atm",
    "glass_type",
    "movement_type",
]

# Map CSV column names to spec keys
CSV_TO_SPEC_KEY = {
    "case_diameter_mm": "case_diameter_mm",
    "gender": "gender",
    "water_resistance_atm": "water_resistance_atm",
    "glass_type": "glass_type",
    "movement_type": "movement_type",
    "case_thickness_mm": "case_thickness_mm",
    "lug_width_mm": "lug_width_mm",
    "lug_to_lug_mm": "lug_to_lug_mm",
    "chronometer": "chronometer",
    "case_color": "case_color",
    "dial_type": "dial_type",
    "case_back": "case_back",
}


def parse_float(value):
    """Parse float value, return None if empty or invalid."""
    if not value or value.strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_decimal(value):
    """Parse decimal value, return None if empty or invalid."""
    if not value or value.strip() == "":
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None


def parse_string(value):
    """Parse string value, return None if empty."""
    if not value or value.strip() == "":
        return None
    return value.strip()


def get_session_with_retry(engine, max_retries=3, retry_delay=2):
    """Get a database session with retry logic."""
    for attempt in range(max_retries):
        try:
            Session = sessionmaker(bind=engine)
            session = Session()
            # Test connection
            session.execute(text("SELECT 1"))
            return session
        except (OperationalError, DisconnectionError) as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Connection failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise


def main():
    """Main seed function."""
    csv_path = Path(__file__).parent.parent / "watch_core_phase1_abtsaat.csv"
    
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)

    # Create engine with connection pooling and retry settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        pool_size=5,         # Connection pool size
        max_overflow=10,    # Max overflow connections
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Found {len(rows)} rows in CSV")

        inserted_count = 0
        updated_count = 0
        batch_size = 50  # Commit every 50 rows instead of 100

        # Initialize session
        session = get_session_with_retry(engine)
        
        for idx, row in enumerate(rows, 1):
            try:
                # Get fresh session for each batch to avoid stale connections
                if (idx - 1) % batch_size == 0 and idx > 1:
                    try:
                        session.commit()
                        session.close()
                    except:
                        pass
                    session = get_session_with_retry(engine)
                
                watch_id = int(row["watch_id"])
                
                # Use no_autoflush to prevent premature flushes during queries
                with session.no_autoflush:
                    # Check if watch already exists
                    existing = session.query(WatchCore).filter(WatchCore.watch_id == watch_id).first()
                
                if existing:
                    # Update existing watch
                    existing.source = row["source"]
                    existing.product_url = row["product_url"]
                    existing.image_url = parse_string(row.get("image_url"))
                    existing.brand = parse_string(row.get("brand"))
                    existing.product_name = row["product_name"]
                    existing.sku = parse_string(row.get("sku"))
                    existing.price_raw = parse_string(row.get("price_raw"))
                    existing.price_value = parse_decimal(row.get("price_value"))
                    existing.currency = row.get("currency", "TRY").upper()
                    existing.description = parse_string(row.get("description"))
                    updated_count += 1
                else:
                    # Create new watch
                    watch = WatchCore(
                        watch_id=watch_id,
                        source=row["source"],
                        product_url=row["product_url"],
                        image_url=parse_string(row.get("image_url")),
                        brand=parse_string(row.get("brand")),
                        product_name=row["product_name"],
                        sku=parse_string(row.get("sku")),
                        price_raw=parse_string(row.get("price_raw")),
                        price_value=parse_decimal(row.get("price_value")),
                        currency=row.get("currency", "TRY").upper(),
                        description=parse_string(row.get("description")),
                    )
                    session.add(watch)
                    inserted_count += 1

                # Create spec sources and initial spec state for each spec key
                for csv_key, spec_key in CSV_TO_SPEC_KEY.items():
                    value = row.get(csv_key)
                    
                    if value and value.strip():
                        spec_value = str(value).strip()
                        
                        # Create or update spec source
                        source = (
                            session.query(WatchSpecSource)
                            .filter(
                                WatchSpecSource.watch_id == watch_id,
                                WatchSpecSource.spec_key == spec_key,
                                WatchSpecSource.source_type == "scraper",
                                WatchSpecSource.source_name == "abtsaat.com",
                                WatchSpecSource.spec_value == spec_value,
                            )
                            .first()
                        )
                        
                        if not source:
                            source = WatchSpecSource(
                                watch_id=watch_id,
                                spec_key=spec_key,
                                spec_value=spec_value,
                                unit=None,  # Can be extracted later if needed
                                source_type="scraper",
                                source_name="abtsaat.com",
                                source_url=row.get("product_url"),
                            )
                            session.add(source)

                        # Create initial spec state (will be resolved later)
                        spec_state = (
                            session.query(WatchSpecState)
                            .filter(
                                WatchSpecState.watch_id == watch_id,
                                WatchSpecState.spec_key == spec_key,
                            )
                            .first()
                        )
                        
                        if not spec_state:
                            # Determine source type: if it's a required field and has value, mark as official
                            source_type = "official" if spec_key in REQUIRED_SPEC_KEYS else "official"
                            
                            spec_state = WatchSpecState(
                                watch_id=watch_id,
                                spec_key=spec_key,
                                spec_value=spec_value,
                                unit=None,
                                source_type=source_type,
                                confidence=None,
                            )
                            session.add(spec_state)
                        else:
                            # Update if value changed
                            if spec_state.spec_value != spec_value:
                                spec_state.spec_value = spec_value
                                spec_state.source_type = "official"

                # Commit every batch_size rows
                if idx % batch_size == 0:
                    try:
                        session.commit()
                        print(f"✅ Processed {idx}/{len(rows)} watches... (Inserted: {inserted_count}, Updated: {updated_count})")
                    except (OperationalError, DisconnectionError) as e:
                        print(f"⚠️  Connection error during commit at row {idx}, retrying...")
                        session.rollback()
                        session = get_session_with_retry(engine)
                        # Re-process the current row
                        continue
                        
            except (OperationalError, DisconnectionError) as e:
                print(f"⚠️  Connection error at row {idx}, retrying...")
                try:
                    session.rollback()
                except:
                    pass
                session = get_session_with_retry(engine)
                # Re-process the current row
                idx -= 1
                continue
            except Exception as e:
                print(f"❌ Error processing row {idx} (watch_id={row.get('watch_id', 'unknown')}): {e}")
                try:
                    session.rollback()
                except:
                    pass
                # Continue with next row
                continue

        # Final commit
        try:
            session.commit()
            print(f"\n✅ Seed completed!")
            print(f"  Inserted: {inserted_count} watches")
            print(f"  Updated: {updated_count} watches")
            print(f"  Total: {inserted_count + updated_count} watches")
        except Exception as e:
            print(f"⚠️  Error during final commit: {e}")
            session.rollback()

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            session.close()
        except:
            pass


if __name__ == "__main__":
    main()

