"""Authentication router using Supabase."""

import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional

import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.clients.supabase_client import get_supabase_client

router = APIRouter()
security = HTTPBearer()


# --- Schemas ---


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: Optional[str] = None


# --- Helper Functions ---


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify JWT token and return user info."""
    token = credentials.credentials
    supabase = get_supabase_client()

    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user.user.id, "email": user.user.email}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# --- Endpoints ---


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """Create a new user account."""
    supabase = get_supabase_client()

    try:
        response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        if not response.user:
            raise HTTPException(status_code=400, detail="Signup failed")

        return AuthResponse(
            access_token=response.session.access_token if response.session else "",
            refresh_token=response.session.refresh_token if response.session else "",
            user_id=response.user.id,
            email=response.user.email or "",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    supabase = get_supabase_client()

    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email or "",
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout current user."""
    supabase = get_supabase_client()

    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse(
        id=user["id"],
        email=user["email"],
    )


@router.post("/auth/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    supabase = get_supabase_client()

    try:
        response = supabase.auth.refresh_session(refresh_token)

        if not response.user or not response.session:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user_id=response.user.id,
            email=response.user.email or "",
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
