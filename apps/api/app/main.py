"""Main FastAPI application."""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.routers import watches, contributions, resolver, ai

app = FastAPI(
    title="Watch Community Platform API",
    description="API for watch enthusiasts community platform",
    version="0.1.0",
)

_static_dir = Path(__file__).parent.parent / "static"
_static_dir.mkdir(exist_ok=True)
(_static_dir / "debug").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(watches.router)
app.include_router(contributions.router)
app.include_router(resolver.router)
app.include_router(ai.router)


@app.get("/")
async def root(request: Request):
    """Root endpoint. Returns HTML in browser, JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(
            content="""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Watch Platform API</title></head>
<body style="font-family: system-ui; max-width: 40rem; margin: 4rem auto; padding: 0 1rem;">
  <h1>Watch Community Platform API</h1>
  <p>This is the backend API. Use the web app to browse watches.</p>
  <ul>
    <li><a href="http://localhost:3000">Open the app (frontend) &rarr; http://localhost:3000</a></li>
    <li><a href="/docs">API docs (Swagger) &rarr; /docs</a></li>
    <li><a href="/health">Health check &rarr; /health</a></li>
  </ul>
</body>
</html>"""
        )
    return {"message": "Watch Community Platform API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

