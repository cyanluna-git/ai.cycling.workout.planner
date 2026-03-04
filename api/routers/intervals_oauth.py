"""Intervals.icu OAuth 2.0 router.

Handles the OAuth authorization flow:
  1. GET  /api/auth/intervals/url       — Generate authorize URL + state
  2. POST /api/auth/intervals/callback   — Exchange code for access token
  3. POST /api/auth/intervals/disconnect — Clear stored OAuth tokens
  4. GET  /api/auth/intervals/status     — Check connection status
"""

import base64
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.clients.supabase_client import get_supabase_admin_client
from .auth import get_current_user
from api.services.cache_service import clear_user_cache

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Configuration ---

INTERVALS_CLIENT_ID = os.getenv("INTERVALS_OAUTH_CLIENT_ID")
if not INTERVALS_CLIENT_ID:
    raise RuntimeError("INTERVALS_OAUTH_CLIENT_ID env var is required")

INTERVALS_CLIENT_SECRET = os.getenv("INTERVALS_OAUTH_CLIENT_SECRET", "")

INTERVALS_REDIRECT_URI = os.getenv("INTERVALS_OAUTH_REDIRECT_URI")
if not INTERVALS_REDIRECT_URI:
    raise RuntimeError(
        "INTERVALS_OAUTH_REDIRECT_URI env var is required "
        "(e.g. http://localhost:3101/auth/callback for local dev)"
    )
INTERVALS_OAUTH_AUTHORIZE_URL = "https://intervals.icu/oauth/authorize"
INTERVALS_OAUTH_TOKEN_URL = "https://intervals.icu/api/oauth/token"
OAUTH_STATE_TTL_MINUTES = 10

# --- Schemas ---


class OAuthUrlResponse(BaseModel):
    authorize_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str


class OAuthCallbackResponse(BaseModel):
    success: bool
    athlete_id: str


class OAuthStatusResponse(BaseModel):
    connected: bool
    method: str  # "oauth", "api_key", or "none"
    athlete_id: str | None = None


# --- Endpoints ---


@router.get("/auth/intervals/url", response_model=OAuthUrlResponse)
async def get_oauth_url(user: dict = Depends(get_current_user)):
    """Generate Intervals.icu OAuth authorize URL with CSRF state."""
    state = str(uuid.uuid4())
    supabase = get_supabase_admin_client()

    # Upsert state into user_api_keys
    supabase.table("user_api_keys").upsert(
        {
            "user_id": user["id"],
            "oauth_state": state,
            "oauth_state_created_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="user_id",
    ).execute()

    authorize_url = (
        f"{INTERVALS_OAUTH_AUTHORIZE_URL}"
        f"?client_id={INTERVALS_CLIENT_ID}"
        f"&redirect_uri={INTERVALS_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=ACTIVITY:READ,WELLNESS:READ,CALENDAR:WRITE,SETTINGS:READ"
        f"&state={state}"
    )

    return OAuthUrlResponse(authorize_url=authorize_url, state=state)


@router.post("/auth/intervals/callback", response_model=OAuthCallbackResponse)
async def oauth_callback(
    body: OAuthCallbackRequest,
    user: dict = Depends(get_current_user),
):
    """Exchange authorization code for access token and save credentials."""
    supabase = get_supabase_admin_client()

    # Fetch stored state
    result = (
        supabase.table("user_api_keys")
        .select("oauth_state, oauth_state_created_at")
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    data = result.data if result else None
    if not data or not data.get("oauth_state"):
        raise HTTPException(status_code=400, detail="No pending OAuth state found.")

    # Verify state matches
    if data["oauth_state"] != body.state:
        raise HTTPException(status_code=400, detail="OAuth state mismatch.")

    # Verify state TTL (<=10 min)
    state_created = datetime.fromisoformat(data["oauth_state_created_at"])
    if state_created.tzinfo is None:
        state_created = state_created.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - state_created > timedelta(minutes=OAUTH_STATE_TTL_MINUTES):
        raise HTTPException(status_code=400, detail="OAuth state expired. Please try again.")

    # Exchange code for token
    credentials = base64.b64encode(
        f"{INTERVALS_CLIENT_ID}:{INTERVALS_CLIENT_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            INTERVALS_OAUTH_TOKEN_URL,
            data={
                "client_id": INTERVALS_CLIENT_ID,
                "client_secret": INTERVALS_CLIENT_SECRET,
                "code": body.code,
                "grant_type": "authorization_code",
                "redirect_uri": INTERVALS_REDIRECT_URI,
            },
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )

    if token_response.status_code != 200:
        logger.error(
            f"OAuth token exchange failed: {token_response.status_code} "
            f"{token_response.text}"
        )
        raise HTTPException(
            status_code=400,
            detail="Failed to exchange authorization code. Please try again.",
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    # Intervals.icu returns athlete as a dict {"id": "i154786", "name": "..."}
    athlete_data = token_data.get("athlete")
    if isinstance(athlete_data, dict):
        athlete_id = athlete_data.get("id")
    else:
        athlete_id = athlete_data

    if not access_token or not athlete_id:
        logger.error(f"OAuth token response missing fields: {list(token_data.keys())}")
        raise HTTPException(
            status_code=400,
            detail="Invalid token response from Intervals.icu.",
        )

    # Save token + athlete_id, clear state
    supabase.table("user_api_keys").upsert(
        {
            "user_id": user["id"],
            "intervals_access_token": access_token,
            "intervals_oauth_athlete_id": str(athlete_id),
            "oauth_state": None,
            "oauth_state_created_at": None,
        },
        on_conflict="user_id",
    ).execute()

    # Clear cache so new credentials are used immediately
    clear_user_cache(user["id"])

    logger.info(f"OAuth connected for user {user['id']}, athlete {athlete_id}")

    return OAuthCallbackResponse(success=True, athlete_id=str(athlete_id))


@router.post("/auth/intervals/disconnect")
async def disconnect_oauth(user: dict = Depends(get_current_user)):
    """Disconnect Intervals.icu OAuth — clear stored tokens."""
    supabase = get_supabase_admin_client()

    supabase.table("user_api_keys").upsert(
        {
            "user_id": user["id"],
            "intervals_access_token": None,
            "intervals_oauth_athlete_id": None,
            "intervals_refresh_token": None,
            "intervals_api_key": None,
            "athlete_id": None,
        },
        on_conflict="user_id",
    ).execute()

    clear_user_cache(user["id"])
    logger.info(
        f"OAuth disconnected for user {user['id']}. "
        "Webhook events for this athlete will be ignored (athlete_id lookup returns no user)."
    )

    return {"success": True}


@router.get("/auth/intervals/status", response_model=OAuthStatusResponse)
async def get_oauth_status(user: dict = Depends(get_current_user)):
    """Check Intervals.icu connection status."""
    supabase = get_supabase_admin_client()

    result = (
        supabase.table("user_api_keys")
        .select(
            "intervals_api_key, athlete_id, "
            "intervals_access_token, intervals_oauth_athlete_id"
        )
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )

    data = result.data if result else {}

    # Check OAuth first
    if data.get("intervals_access_token") and data.get("intervals_oauth_athlete_id"):
        return OAuthStatusResponse(
            connected=True,
            method="oauth",
            athlete_id=data["intervals_oauth_athlete_id"],
        )

    # Check legacy API key
    if data.get("intervals_api_key") and data.get("athlete_id"):
        return OAuthStatusResponse(
            connected=True,
            method="api_key",
            athlete_id=data["athlete_id"],
        )

    return OAuthStatusResponse(connected=False, method="none", athlete_id=None)
