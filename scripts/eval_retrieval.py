#!/usr/bin/env python3
"""
Evaluation and threshold tuning pipeline for retrieval system.

Computes score distributions and recommends optimal thresholds:
- SIM_TOP1_MIN: Minimum top-1 similarity score
- SIM_GAP_MIN: Minimum gap between top-1 and top-2 scores

Prioritizes very low false positives over coverage.
"""

import csv
import os
import sys
import random
import argparse
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from decimal import Decimal

import httpx
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "apps" / "api"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import WatchCore

# Load environment variables
load_dotenv(project_root / ".env")
load_dotenv(project_root / "apps" / "api" / ".env", override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Create reports directory
REPORTS_DIR = project_root / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def get_db_session():
    """Create database session."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set in environment")
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


def load_image_manifest() -> Dict[int, List[str]]:
    """Load image manifest CSV to get local image paths per watch."""
    manifest_path = project_root / "image_manifest.csv"
    if not manifest_path.exists():
        return {}
    
    manifest = {}
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            watch_id = int(row['watch_id'])
            local_path = row.get('local_path', '')
            if local_path and local_path != 'failed':
                if watch_id not in manifest:
                    manifest[watch_id] = []
                # Convert relative path to absolute
                full_path = project_root / local_path
                if full_path.exists():
                    manifest[watch_id].append(str(full_path))
    
    return manifest


def get_watch_images(watch: WatchCore, image_manifest: Dict[int, List[str]]) -> List[str]:
    """Get available images for a watch (from DB or manifest)."""
    images = []
    
    # First, try local manifest
    if watch.watch_id in image_manifest:
        images.extend(image_manifest[watch.watch_id])
    
    # Also check image_url from database
    if watch.image_url:
        urls = [url.strip() for url in watch.image_url.split() if url.strip()]
        images.extend(urls)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_images = []
    for img in images:
        if img not in seen:
            seen.add(img)
            unique_images.append(img)
    
    return unique_images


def sample_watches(session, n: int, seed: int = 42) -> List[WatchCore]:
    """Sample N watches deterministically."""
    random.seed(seed)
    
    # Get all watches with images
    watches = session.query(WatchCore).filter(
        WatchCore.image_url.isnot(None)
    ).all()
    
    if len(watches) < n:
        print(f"Warning: Only {len(watches)} watches available, requested {n}")
        return watches
    
    return random.sample(watches, n)


def call_identify_api(image_path_or_url: str, api_url: str, timeout: int = 30) -> Optional[Dict]:
    """Call /ai/identify endpoint."""
    try:
        # Determine if it's a file path or URL
        is_file = False
        if not image_path_or_url.startswith('http'):
            path = Path(image_path_or_url)
            if path.exists() and path.is_file():
                is_file = True
        
        with httpx.Client(timeout=timeout) as client:
            if is_file:
                # Upload file
                with open(image_path_or_url, 'rb') as f:
                    files = {'image_file': (Path(image_path_or_url).name, f, 'image/jpeg')}
                    data = {
                        'top_k': '10',
                        'use_vlm': 'false',
                    }
                    response = client.post(
                        f"{api_url}/ai/identify",
                        files=files,
                        data=data
                    )
            else:
                # Use URL - FastAPI Form expects form data (strings)
                data = {
                    'image_url': image_path_or_url,
                    'top_k': '10',
                    'use_vlm': 'false',
                }
                response = client.post(
                    f"{api_url}/ai/identify",
                    data=data
                )
            
            response.raise_for_status()
            return response.json()
    
    except httpx.HTTPStatusError as e:
        print(f"  ❌ API returned {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        print(f"  ❌ Error calling API: {e}")
        return None


def evaluate_retrieval(session, n_watches: int = 50, seed: int = 42, api_url: str = API_URL) -> pd.DataFrame:
    """Run evaluation on sampled watches."""
    print(f"📊 Starting retrieval evaluation (N={n_watches}, seed={seed})")
    
    # Load image manifest
    image_manifest = load_image_manifest()
    print(f"✅ Loaded {len(image_manifest)} watches from image manifest")
    
    # Sample watches
    watches = sample_watches(session, n_watches, seed)
    print(f"✅ Sampled {len(watches)} watches")
    
    results = []
    
    for idx, watch in enumerate(watches, 1):
        print(f"\n[{idx}/{len(watches)}] Evaluating watch_id={watch.watch_id} ({watch.product_name})")
        
        # Get available images
        images = get_watch_images(watch, image_manifest)
        
        if not images:
            print(f"  ⚠️  No images available, skipping")
            continue
        
        # Pick first image as query
        query_image = images[0]
        print(f"  📷 Using image: {query_image[:80]}...")
        
        # Call API
        start_time = time.time()
        response = call_identify_api(query_image, api_url)
        elapsed = time.time() - start_time
        
        if not response:
            print(f"  ❌ API call failed")
            continue
        
        candidates = response.get('candidates', [])
        is_unknown = response.get('is_unknown', False) or response.get('unknown_watch', False)
        
        if is_unknown or len(candidates) == 0:
            print(f"  ⚠️  No candidates returned (unknown watch: {is_unknown})")
            results.append({
                'watch_id': watch.watch_id,
                'expected_watch_id': watch.watch_id,
                'top1_watch_id': None,
                'top1_score': None,
                'top2_watch_id': None,
                'top2_score': None,
                'gap': None,
                'is_correct': False,
                'api_time_ms': int(elapsed * 1000),
            })
            continue
        
        # Extract top results
        top1 = candidates[0] if len(candidates) > 0 else None
        top2 = candidates[1] if len(candidates) > 1 else None
        
        top1_watch_id = top1['watch_id'] if top1 else None
        top1_score = top1['similarity_score'] if top1 else None
        top2_watch_id = top2['watch_id'] if top2 else None
        top2_score = top2['similarity_score'] if top2 else None
        
        gap = (top1_score - top2_score) if (top1_score is not None and top2_score is not None) else None
        is_correct = (top1_watch_id == watch.watch_id) if top1_watch_id else False
        
        print(f"  ✅ Top1: watch_id={top1_watch_id}, score={top1_score:.4f}, correct={is_correct}")
        if top2:
            print(f"     Top2: watch_id={top2_watch_id}, score={top2_score:.4f}, gap={gap:.4f}")
        
        results.append({
            'watch_id': watch.watch_id,
            'expected_watch_id': watch.watch_id,
            'top1_watch_id': top1_watch_id,
            'top1_score': top1_score,
            'top2_watch_id': top2_watch_id,
            'top2_score': top2_score,
            'gap': gap,
            'is_correct': is_correct,
            'api_time_ms': int(elapsed * 1000),
        })
    
    # Ensure DataFrame has all expected columns even if empty
    expected_columns = [
        'watch_id', 'expected_watch_id', 'top1_watch_id', 'top1_score',
        'top2_watch_id', 'top2_score', 'gap', 'is_correct', 'api_time_ms'
    ]
    
    if len(results) == 0:
        # Return empty DataFrame with correct columns
        df = pd.DataFrame(columns=expected_columns)
    else:
        df = pd.DataFrame(results)
        # Ensure all columns exist
        for col in expected_columns:
            if col not in df.columns:
                df[col] = None
    
    return df


def grid_search_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    """Perform grid search over threshold combinations."""
    print("\n🔍 Starting threshold grid search...")
    
    # Filter out rows with missing data
    valid_df = df.dropna(subset=['top1_score', 'gap', 'is_correct'])
    
    if len(valid_df) == 0:
        print("⚠️  No valid data for grid search")
        return pd.DataFrame()
    
    n_total = len(valid_df)
    
    # Grid search parameters
    sim_top1_min_range = [round(x, 2) for x in [i * 0.02 for i in range(28, 43)]]  # 0.55 to 0.85 step 0.02
    sim_gap_min_range = [round(x, 2) for x in [i * 0.01 for i in range(0, 11)]]  # 0.00 to 0.10 step 0.01
    
    grid_results = []
    
    for sim_top1_min in sim_top1_min_range:
        for sim_gap_min in sim_gap_min_range:
            # Apply thresholds
            matched = valid_df[
                (valid_df['top1_score'] >= sim_top1_min) &
                (valid_df['gap'] >= sim_gap_min)
            ]
            
            n_matched = len(matched)
            
            if n_matched == 0:
                # No matches, skip
                continue
            
            n_correct = matched['is_correct'].sum()
            n_false_positive = n_matched - n_correct
            
            false_positive_rate = n_false_positive / n_matched if n_matched > 0 else 0.0
            coverage = n_matched / n_total if n_total > 0 else 0.0
            accuracy_matched = n_correct / n_matched if n_matched > 0 else 0.0
            
            grid_results.append({
                'sim_top1_min': sim_top1_min,
                'sim_gap_min': sim_gap_min,
                'n_matched': n_matched,
                'n_correct': n_correct,
                'n_false_positive': n_false_positive,
                'false_positive_rate': false_positive_rate,
                'coverage': coverage,
                'accuracy_matched': accuracy_matched,
            })
    
    grid_df = pd.DataFrame(grid_results)
    return grid_df


def find_best_thresholds(grid_df: pd.DataFrame) -> Optional[Dict]:
    """Find best threshold combination based on criteria."""
    if len(grid_df) == 0:
        return None
    
    # Filter: false_positive_rate <= 0.01 (1%)
    valid = grid_df[grid_df['false_positive_rate'] <= 0.01].copy()
    
    if len(valid) == 0:
        print("⚠️  No thresholds found with false_positive_rate <= 1%")
        # Fall back to best available
        valid = grid_df.copy()
    
    if len(valid) == 0:
        return None
    
    # Sort by: 1) minimize false_positive_rate, 2) maximize accuracy_matched, 3) maximize coverage
    valid = valid.sort_values(
        by=['false_positive_rate', 'accuracy_matched', 'coverage'],
        ascending=[True, False, False]
    )
    
    best = valid.iloc[0].to_dict()
    return best


def main():
    parser = argparse.ArgumentParser(description='Evaluate retrieval system and tune thresholds')
    parser.add_argument('--n', type=int, default=50, help='Number of watches to sample (default: 50)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for sampling (default: 42)')
    parser.add_argument('--api-url', type=str, default=API_URL, help=f'API URL (default: {API_URL})')
    parser.add_argument('--skip-eval', action='store_true', help='Skip evaluation, only run grid search on existing data')
    
    args = parser.parse_args()
    
    # Check API is running
    if not args.skip_eval:
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{args.api_url}/health", timeout=5)
                if response.status_code != 200:
                    print(f"⚠️  API health check failed, but continuing...")
        except Exception as e:
            print(f"⚠️  Could not reach API at {args.api_url}: {e}")
            print("   Make sure the API is running: npm run dev:api")
            sys.exit(1)
    
    session = get_db_session()
    
    try:
        # Pre-check: Verify embeddings exist
        if not args.skip_eval:
            from app.models import WatchEmbedding
            embedding_count = session.query(WatchEmbedding).filter(
                WatchEmbedding.embedding.isnot(None)
            ).count()
            
            if embedding_count == 0:
                print("⚠️  WARNING: No watch embeddings found in database!")
                print("   The API will likely return 500 errors.")
                print("   Run the embedding endpoint first:")
                print("   curl -X POST http://localhost:8000/ai/embed_watch_images")
                print("   Continuing anyway...\n")
            else:
                print(f"✅ Found {embedding_count} watch embeddings in database\n")
        
        # Run evaluation
        if args.skip_eval:
            print("⏭️  Skipping evaluation, loading existing data...")
            raw_path = REPORTS_DIR / "retrieval_eval_raw.csv"
            if not raw_path.exists():
                print(f"❌ {raw_path} not found. Run without --skip-eval first.")
                sys.exit(1)
            df = pd.read_csv(raw_path)
        else:
            df = evaluate_retrieval(session, args.n, args.seed, args.api_url)
            
            # Save raw results
            raw_path = REPORTS_DIR / "retrieval_eval_raw.csv"
            df.to_csv(raw_path, index=False)
            print(f"\n✅ Saved raw results to {raw_path}")
        
        # Print summary statistics
        print("\n" + "="*60)
        print("📈 SUMMARY STATISTICS")
        print("="*60)
        
        if len(df) == 0:
            print("⚠️  No evaluation results available (all API calls failed)")
            print("\nTroubleshooting:")
            print("  1. Check that API is running: npm run dev:api")
            print("  2. Check API logs for error details")
            print("  3. Verify AI service is available (transformers, torch installed)")
            print("  4. Verify watch embeddings exist in database")
        else:
            # Check if we have the required columns
            required_cols = ['top1_score', 'is_correct']
            if all(col in df.columns for col in required_cols):
                valid_df = df.dropna(subset=required_cols)
                if len(valid_df) > 0:
                    print(f"Total queries: {len(df)}")
                    print(f"Successful queries: {len(valid_df)}")
                    print(f"Failed queries: {len(df) - len(valid_df)}")
                    print(f"\nCorrect top-1: {valid_df['is_correct'].sum()} ({valid_df['is_correct'].mean()*100:.1f}%)")
                    print(f"Mean top-1 score: {valid_df['top1_score'].mean():.4f}")
                    if 'gap' in valid_df.columns:
                        gap_mean = valid_df['gap'].mean()
                        if pd.notna(gap_mean):
                            print(f"Mean gap: {gap_mean:.4f}")
                    if 'api_time_ms' in valid_df.columns:
                        time_mean = valid_df['api_time_ms'].mean()
                        if pd.notna(time_mean):
                            print(f"Mean API time: {time_mean:.0f}ms")
                else:
                    print(f"Total queries: {len(df)}")
                    print("⚠️  No valid results (all queries failed or returned no candidates)")
            else:
                print(f"⚠️  DataFrame missing required columns: {required_cols}")
                print(f"Available columns: {list(df.columns)}")
        
        # Grid search
        grid_df = grid_search_thresholds(df)
        
        if len(grid_df) > 0:
            # Save grid results
            grid_path = REPORTS_DIR / "threshold_grid.csv"
            grid_df.to_csv(grid_path, index=False)
            print(f"\n✅ Saved grid search results to {grid_path}")
            
            # Find best thresholds
            best = find_best_thresholds(grid_df)
            
            if best:
                print("\n" + "="*60)
                print("🎯 RECOMMENDED THRESHOLDS")
                print("="*60)
                print(f"SIM_TOP1_MIN = {best['sim_top1_min']:.2f}")
                print(f"SIM_GAP_MIN = {best['sim_gap_min']:.2f}")
                print(f"\nMetrics at these thresholds:")
                print(f"  False Positive Rate: {best['false_positive_rate']*100:.2f}%")
                print(f"  Coverage: {best['coverage']*100:.1f}%")
                print(f"  Accuracy (matched): {best['accuracy_matched']*100:.1f}%")
                print(f"  Matched queries: {best['n_matched']}/{len(df)}")
            else:
                print("\n⚠️  Could not determine best thresholds")
        else:
            print("\n⚠️  Grid search produced no results")
    
    finally:
        session.close()


if __name__ == "__main__":
    main()
