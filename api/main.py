"""FastAPI Backend for AI Cycling Coach.

REST API endpoints for the React frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import workout, fitness

app = FastAPI(
    title="AI Cycling Coach API",
    description="REST API for AI-powered cycling workout generation",
    version="1.0.0",
)

# CORS configuration for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "https://*.vercel.app",  # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(fitness.router, prefix="/api", tags=["fitness"])
app.include_router(workout.router, prefix="/api", tags=["workout"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Cycling Coach API"}


@app.get("/api/health")
async def health():
    """Health check for Railway."""
    return {"status": "healthy"}
