#!/usr/bin/env bash
# Run the FastAPI app with a Python that has uvicorn.
# Tries: apps/api/.venv, then conda env (saat_app or CONDA_ENV), then python3/python.
set -e
cd "$(dirname "$0")/../apps/api"

if [ -x ".venv/bin/python" ]; then
  exec .venv/bin/python -m uvicorn app.main:app --reload --port 8000
fi

CONDA_ENV_NAME="${CONDA_ENV:-saat_app}"
if command -v conda &>/dev/null; then
  if conda run -n "$CONDA_ENV_NAME" python -c "import uvicorn" 2>/dev/null; then
    exec conda run -n "$CONDA_ENV_NAME" python -m uvicorn app.main:app --reload --port 8000
  fi
fi

if command -v python3 &>/dev/null && python3 -c "import uvicorn" 2>/dev/null; then
  exec python3 -m uvicorn app.main:app --reload --port 8000
fi

exec python -m uvicorn app.main:app --reload --port 8000
