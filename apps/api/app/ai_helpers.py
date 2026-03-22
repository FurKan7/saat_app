"""
Helpers to import the shared AI modules under `apps/ai`.

Your project structure:
  - apps/api/app/...
  - apps/ai/...

Routers often inject `apps/ai` into sys.path manually. For background workers,
we centralize that logic here so we don't repeat it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple, Any


def _ensure_ai_path_on_sys_path() -> None:
    # apps/api/app/ai_helpers.py -> parents:
    # 0 app, 1 api, 2 apps, 3 repo root
    repo_root = Path(__file__).resolve().parents[3]
    ai_dir = repo_root / "apps" / "ai"
    if str(ai_dir) not in sys.path:
        sys.path.insert(0, str(ai_dir))


def safe_ai_imports() -> Tuple[Any, Any, Any]:
    """
    Import and return:
      - embedder module
      - detector module
      - vlm module
    """
    _ensure_ai_path_on_sys_path()
    import embedder
    import detector
    import vlm
    return embedder, detector, vlm

