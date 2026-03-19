import os
import re
import csv
import time
import hashlib
from urllib.parse import urlparse

import pandas as pd
import requests

INPUT_CSV = "watch_core_phase1_abtsaat.csv"   # aynı klasördeyse
OUT_DIR = "watch_images"                      # kök klasör
MANIFEST_PATH = "image_manifest.csv"
FAILED_PATH = "image_failed.csv"

# İndirme ayarları
TIMEOUT = 25
RETRIES = 3
SLEEP_BETWEEN = 0.5  # siteyi yormamak için
USER_AGENT = "Mozilla/5.0 (compatible; WatchDatasetBot/1.0; +local-backup)"

def safe_name(s: str, max_len: int = 80) -> str:
    """Dosya/klasör için güvenli isim."""
    if s is None:
        return "unknown"
    s = str(s).strip()
    if not s:
        return "unknown"
    s = s.lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^\w\s\.-]+", "_", s)   # unicode word chars ok
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:max_len] if len(s) > max_len else s

def infer_model_folder(product_name: str, brand: str, sku: str) -> str:
    """
    Model klasörü için basit heuristic.
    - sku varsa onu tercih et
    - yoksa product_name içinden brand’i atıp kalan ilk 6 token
    """
    if sku and str(sku).strip():
        return safe_name(str(sku).strip(), 60)

    pn = str(product_name or "").strip()
    br = str(brand or "").strip()

    if br and pn.lower().startswith(br.lower()):
        rest = pn[len(br):].strip()
    else:
        rest = pn

    tokens = re.findall(r"[A-Za-z0-9]+", rest)
    if not tokens:
        return "unknown_model"
    model = "_".join(tokens[:6])
    return safe_name(model, 60)

def get_ext_from_url(url: str) -> str:
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    ext = ext.lower().strip()
    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        return ext
    return ".jpg"  # fallback

def download_one(session: requests.Session, url: str, out_path: str) -> bool:
    for attempt in range(1, RETRIES + 1):
        try:
            r = session.get(url, timeout=TIMEOUT, stream=True)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            if attempt == RETRIES:
                return False
            time.sleep(0.8 * attempt)
    return False

def main():
    df = pd.read_csv(INPUT_CSV)

    # Beklenen kolonlar: watch_id, brand, product_name, sku, image_url
    needed = ["watch_id", "brand", "product_name", "sku", "image_url"]
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Missing column: {c}")

    os.makedirs(OUT_DIR, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    manifest_rows = []
    failed_rows = []

    for i, row in df.iterrows():
        watch_id = row.get("watch_id")
        brand = row.get("brand")
        product_name = row.get("product_name")
        sku = row.get("sku")
        url = row.get("image_url")

        if not isinstance(url, str) or not url.strip():
            failed_rows.append({
                "watch_id": watch_id,
                "image_url": url,
                "reason": "empty_image_url"
            })
            continue

        brand_folder = safe_name(brand, 60)
        model_folder = infer_model_folder(product_name, brand, sku)

        ext = get_ext_from_url(url)
        # URL hash ile çakışma önleme
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]

        sku_part = safe_name(sku, 40) if isinstance(sku, str) and sku.strip() else "no_sku"
        filename = f"watch_{int(watch_id)}__{sku_part}__{url_hash}{ext}"

        out_path = os.path.join(OUT_DIR, brand_folder, model_folder, filename)

        # zaten varsa indirme
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            manifest_rows.append({
                "watch_id": watch_id,
                "brand": brand,
                "product_name": product_name,
                "sku": sku,
                "image_url": url,
                "local_path": out_path,
                "status": "exists"
            })
            continue

        ok = download_one(session, url, out_path)
        if ok:
            manifest_rows.append({
                "watch_id": watch_id,
                "brand": brand,
                "product_name": product_name,
                "sku": sku,
                "image_url": url,
                "local_path": out_path,
                "status": "downloaded"
            })
        else:
            failed_rows.append({
                "watch_id": watch_id,
                "image_url": url,
                "reason": "download_failed"
            })

        time.sleep(SLEEP_BETWEEN)

    # write manifest
    pd.DataFrame(manifest_rows).to_csv(MANIFEST_PATH, index=False, encoding="utf-8")
    pd.DataFrame(failed_rows).to_csv(FAILED_PATH, index=False, encoding="utf-8")

    print(f"Done. downloaded/exists: {len(manifest_rows)}, failed: {len(failed_rows)}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Failed: {FAILED_PATH}")

if __name__ == "__main__":
    main()