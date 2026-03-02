"""FastAPI Backend for AI Cycling Coach.

REST API endpoints for the React frontend.
"""

import subprocess
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import workout, fitness, auth, settings, admin, plans, profiles
from starlette.middleware.base import BaseHTTPMiddleware
from .i18n import get_language

app = FastAPI(
    title="AI Cycling Coach API",
    description="REST API for AI-powered cycling workout generation",
    version="1.0.0",
)

class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        accept_lang = request.headers.get("accept-language", "en")
        request.state.lang = get_language(accept_lang)
        response = await call_next(request)
        return response

# Language detection middleware
app.add_middleware(LanguageMiddleware)

# Request logging middleware for admin monitoring (added BEFORE CORS)
from .middleware import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)

# CORS configuration - 분리 배포용
# Vercel 프론트엔드에서 Render 백엔드로 요청 허용
# NOTE: This must be the LAST middleware added (so it runs FIRST)
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev
    "http://localhost:3101",  # run.sh dev port (frontend)
    "http://localhost:8000",  # Default uvicorn
    "http://localhost:8005",  # Alternative dev port
    "https://*.vercel.app",  # Vercel preview deployments
    "https://ai-cycling-workout-planner.vercel.app",  # Production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use specific origins instead of ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(fitness.router, prefix="/api", tags=["fitness"])
app.include_router(workout.router, prefix="/api", tags=["workout"])
app.include_router(plans.router, prefix="/api", tags=["plans"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(profiles.router, prefix="/api", tags=["profiles"])


def _get_git_info():
    """Get git commit information at startup (env var > git command)."""
    import os
    commit = os.environ.get("GIT_COMMIT")
    commit_date = os.environ.get("GIT_COMMIT_DATE")
    if commit and commit != "unknown":
        return {"commit": commit, "commit_date": commit_date or "unknown"}
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        commit_date = subprocess.check_output(
            ["git", "log", "-1", "--format=%ci"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        return {"commit": commit, "commit_date": commit_date}
    except Exception:
        return {"commit": "unknown", "commit_date": "unknown"}


# Cache git info at startup
_git_info = _get_git_info()
_start_time = datetime.utcnow().isoformat() + "Z"


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Cycling Coach API"}


@app.get("/api/health")
async def health():
    """Health check for deployment."""
    return {
        "status": "healthy",
        "version": app.version,
        "git_commit": _git_info["commit"],
        "git_commit_date": _git_info["commit_date"],
        "started_at": _start_time,
    }


