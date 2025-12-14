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

# CORS configuration - 분리 배포용
# Vercel 프론트엔드에서 Render 백엔드로 요청 허용
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative dev
    "https://*.vercel.app",  # Vercel preview deployments
    # 배포 후 실제 Vercel 도메인 추가 예정
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 중에는 전체 허용, 배포 후 origins로 변경
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
    """Health check for deployment."""
    return {"status": "healthy"}
