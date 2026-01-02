"""Admin API Router.

Protected endpoints for admin/system monitoring.
Requires admin authentication via ADMIN_SECRET environment variable.
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query, Depends
from pydantic import BaseModel

from src.clients.supabase_client import get_supabase_admin_client


router = APIRouter()


def verify_admin_secret(x_admin_secret: Optional[str] = Header(None)) -> None:
    """Verify admin secret from header."""
    admin_secret = os.getenv("ADMIN_SECRET")

    if not admin_secret:
        raise HTTPException(
            status_code=500, detail="ADMIN_SECRET not configured on server"
        )

    if x_admin_secret != admin_secret:
        raise HTTPException(status_code=401, detail="Invalid admin secret")


class AuditLogResponse(BaseModel):
    """Response model for audit logs."""

    id: str
    event_type: str
    user_id: Optional[str]
    details: dict
    ip_address: Optional[str]
    created_at: str


class AuditLogsListResponse(BaseModel):
    """Response model for audit logs list."""

    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


@router.get("/admin/audit-logs", response_model=AuditLogsListResponse)
async def get_audit_logs(
    x_admin_secret: Optional[str] = Header(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
):
    """Get audit logs with pagination and filtering.

    Requires X-Admin-Secret header for authentication.
    """
    verify_admin_secret(x_admin_secret)

    supabase = get_supabase_admin_client()

    # Build query
    query = supabase.table("audit_logs").select("*", count="exact")

    # Apply filters
    if event_type:
        query = query.eq("event_type", event_type)
    if user_id:
        query = query.eq("user_id", user_id)

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

    result = query.execute()

    logs = [
        AuditLogResponse(
            id=log.get("id", ""),
            event_type=log.get("event_type", ""),
            user_id=log.get("user_id"),
            details=log.get("details", {}),
            ip_address=log.get("ip_address"),
            created_at=log.get("created_at", ""),
        )
        for log in (result.data or [])
    ]

    return AuditLogsListResponse(
        logs=logs,
        total=result.count or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/admin/audit-logs/stats")
async def get_audit_stats(
    x_admin_secret: Optional[str] = Header(None),
):
    """Get audit log statistics.

    Returns event counts grouped by type.
    """
    verify_admin_secret(x_admin_secret)

    supabase = get_supabase_admin_client()

    # Get all logs and count by type (Supabase doesn't support GROUP BY directly)
    result = supabase.table("audit_logs").select("event_type").execute()

    event_counts: dict[str, int] = {}
    for log in result.data or []:
        event_type = log.get("event_type", "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    return {
        "event_counts": event_counts,
        "total_events": sum(event_counts.values()),
    }


@router.delete("/admin/audit-logs/cleanup")
async def cleanup_old_logs(
    x_admin_secret: Optional[str] = Header(None),
    days_to_keep: int = Query(30, ge=1, le=365),
):
    """Delete audit logs older than specified days.

    Use with caution - this permanently deletes data.
    """
    verify_admin_secret(x_admin_secret)

    from datetime import datetime, timedelta

    cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()

    supabase = get_supabase_admin_client()

    result = (
        supabase.table("audit_logs").delete().lt("created_at", cutoff_date).execute()
    )

    deleted_count = len(result.data or [])

    return {
        "message": f"Deleted {deleted_count} logs older than {days_to_keep} days",
        "deleted_count": deleted_count,
    }


# ============================================
# LLM Model Management Endpoints
# ============================================


class LLMModelRequest(BaseModel):
    """Request model for creating/updating LLM models."""

    provider: str  # groq, gemini, huggingface, openai
    model_id: str  # e.g., llama-3.3-70b-versatile
    display_name: Optional[str] = None
    is_active: bool = True
    priority: int = 0


class LLMModelResponse(BaseModel):
    """Response model for LLM model."""

    id: str
    provider: str
    model_id: str
    display_name: Optional[str]
    is_active: bool
    priority: int
    created_at: str


@router.get("/admin/llm-models")
async def get_llm_models(
    x_admin_secret: Optional[str] = Header(None),
    provider: Optional[str] = Query(None),
):
    """Get all LLM models, optionally filtered by provider."""
    verify_admin_secret(x_admin_secret)

    supabase = get_supabase_admin_client()

    query = supabase.table("llm_models").select("*").order("priority", desc=True)

    if provider:
        query = query.eq("provider", provider)

    result = query.execute()

    return {
        "models": result.data or [],
        "total": len(result.data or []),
    }


@router.post("/admin/llm-models")
async def create_llm_model(
    model: LLMModelRequest,
    x_admin_secret: Optional[str] = Header(None),
):
    """Create a new LLM model configuration."""
    verify_admin_secret(x_admin_secret)

    supabase = get_supabase_admin_client()

    model_data = {
        "provider": model.provider,
        "model_id": model.model_id,
        "display_name": model.display_name or model.model_id,
        "is_active": model.is_active,
        "priority": model.priority,
    }

    result = supabase.table("llm_models").insert(model_data).execute()

    return {
        "message": "Model created successfully",
        "model": result.data[0] if result.data else None,
    }


@router.put("/admin/llm-models/{model_id}")
async def update_llm_model(
    model_id: str,
    model: LLMModelRequest,
    x_admin_secret: Optional[str] = Header(None),
):
    """Update an existing LLM model configuration."""
    verify_admin_secret(x_admin_secret)

    supabase = get_supabase_admin_client()

    model_data = {
        "provider": model.provider,
        "model_id": model.model_id,
        "display_name": model.display_name or model.model_id,
        "is_active": model.is_active,
        "priority": model.priority,
    }

    result = (
        supabase.table("llm_models").update(model_data).eq("id", model_id).execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "message": "Model updated successfully",
        "model": result.data[0],
    }


@router.delete("/admin/llm-models/{model_id}")
async def delete_llm_model(
    model_id: str,
    x_admin_secret: Optional[str] = Header(None),
):
    """Delete an LLM model configuration."""
    verify_admin_secret(x_admin_secret)

    supabase = get_supabase_admin_client()

    result = supabase.table("llm_models").delete().eq("id", model_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "message": "Model deleted successfully",
    }


@router.patch("/admin/llm-models/{model_id}/toggle")
async def toggle_llm_model(
    model_id: str,
    x_admin_secret: Optional[str] = Header(None),
):
    """Toggle a model's active status."""
    verify_admin_secret(x_admin_secret)

    supabase = get_supabase_admin_client()

    # Get current status
    current = (
        supabase.table("llm_models")
        .select("is_active")
        .eq("id", model_id)
        .single()
        .execute()
    )

    if not current.data:
        raise HTTPException(status_code=404, detail="Model not found")

    new_status = not current.data.get("is_active", True)

    result = (
        supabase.table("llm_models")
        .update({"is_active": new_status})
        .eq("id", model_id)
        .execute()
    )

    return {
        "message": f"Model {'activated' if new_status else 'deactivated'}",
        "is_active": new_status,
    }


# ============================================
# User-Based Admin Verification
# ============================================


async def verify_admin_user(user_id: str) -> bool:
    """Verify if a user has admin privileges."""
    try:
        supabase = get_supabase_admin_client()
        result = (
            supabase.table("user_settings")
            .select("is_admin")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return result.data.get("is_admin", False) if result.data else False
    except Exception:
        return False


def get_admin_user(authorization: Optional[str] = Header(None)) -> str:
    """Dependency to verify admin user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")

    token = authorization[7:]

    try:
        from src.clients.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        user = supabase.auth.get_user(token)

        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user.user.id

        # Check admin status
        admin_supabase = get_supabase_admin_client()
        result = (
            admin_supabase.table("user_settings")
            .select("is_admin")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not result.data or not result.data.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")

        return user_id

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# ============================================
# Statistics Endpoints (User-Based Auth)
# ============================================


@router.get("/admin/stats/overview")
async def get_overview_stats(
    admin_user_id: str = Depends(get_admin_user),
):
    """Get overview statistics for admin dashboard.

    Returns total users, workouts generated today, and API calls.
    """
    from datetime import datetime, timedelta

    supabase = get_supabase_admin_client()
    today = datetime.utcnow().date().isoformat()
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

    # Total users
    users_result = supabase.table("user_settings").select("id", count="exact").execute()
    total_users = users_result.count or 0

    # Workouts generated today (from audit_logs)
    workouts_result = (
        supabase.table("audit_logs")
        .select("id", count="exact")
        .eq("event_type", "workout.generated")
        .gte("created_at", today)
        .execute()
    )
    workouts_today = workouts_result.count or 0

    # API calls today
    api_calls_result = (
        supabase.table("api_request_logs")
        .select("id", count="exact")
        .gte("created_at", today)
        .execute()
    )
    api_calls_today = api_calls_result.count or 0

    # API calls this week
    api_calls_week = (
        supabase.table("api_request_logs")
        .select("id", count="exact")
        .gte("created_at", week_ago)
        .execute()
    )

    # Average response time today
    response_times = (
        supabase.table("api_request_logs")
        .select("response_time_ms")
        .gte("created_at", today)
        .execute()
    )
    avg_response_time = 0
    if response_times.data:
        times = [
            r.get("response_time_ms", 0)
            for r in response_times.data
            if r.get("response_time_ms")
        ]
        avg_response_time = sum(times) // len(times) if times else 0

    return {
        "total_users": total_users,
        "workouts_today": workouts_today,
        "api_calls_today": api_calls_today,
        "api_calls_week": api_calls_week.count or 0,
        "avg_response_time_ms": avg_response_time,
    }


@router.get("/admin/stats/users")
async def get_user_stats(
    admin_user_id: str = Depends(get_admin_user),
    days: int = Query(30, ge=1, le=365),
):
    """Get user statistics.

    Returns user signup trends and active users.
    """
    from datetime import datetime, timedelta

    supabase = get_supabase_admin_client()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    # Get signups from audit logs
    signups = (
        supabase.table("audit_logs")
        .select("created_at")
        .eq("event_type", "user.signup")
        .gte("created_at", cutoff)
        .order("created_at", desc=False)
        .execute()
    )

    # Group by date
    daily_signups: dict[str, int] = {}
    for log in signups.data or []:
        date = log.get("created_at", "")[:10]
        daily_signups[date] = daily_signups.get(date, 0) + 1

    # Active users (have made API calls in last 7 days)
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    active_users = (
        supabase.table("api_request_logs")
        .select("user_id")
        .gte("created_at", week_ago)
        .not_.is_("user_id", "null")
        .execute()
    )

    unique_active = len(
        set(log.get("user_id") for log in active_users.data or [] if log.get("user_id"))
    )

    return {
        "daily_signups": daily_signups,
        "active_users_last_7_days": unique_active,
        "total_signups_period": len(signups.data or []),
    }


@router.get("/admin/stats/workouts")
async def get_workout_stats(
    admin_user_id: str = Depends(get_admin_user),
    days: int = Query(30, ge=1, le=365),
):
    """Get workout generation statistics.

    Returns daily workout counts and trends.
    """
    from datetime import datetime, timedelta

    supabase = get_supabase_admin_client()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    # Get workout generations from audit logs
    workouts = (
        supabase.table("audit_logs")
        .select("created_at, user_id, details")
        .eq("event_type", "workout.generated")
        .gte("created_at", cutoff)
        .order("created_at", desc=False)
        .execute()
    )

    # Group by date
    daily_workouts: dict[str, int] = {}
    for log in workouts.data or []:
        date = log.get("created_at", "")[:10]
        daily_workouts[date] = daily_workouts.get(date, 0) + 1

    # Synced workouts
    synced = (
        supabase.table("audit_logs")
        .select("id", count="exact")
        .eq("event_type", "workout.sync_success")
        .gte("created_at", cutoff)
        .execute()
    )

    return {
        "daily_workouts": daily_workouts,
        "total_generated": len(workouts.data or []),
        "total_synced": synced.count or 0,
    }


# ============================================
# API Request Logs Endpoints
# ============================================


class ApiLogResponse(BaseModel):
    """Response model for API request log."""

    id: str
    user_id: Optional[str]
    method: str
    path: str
    status_code: Optional[int]
    response_time_ms: Optional[int]
    ip_address: Optional[str]
    error_message: Optional[str]
    created_at: str


class ApiLogsListResponse(BaseModel):
    """Response model for API logs list."""

    logs: list[ApiLogResponse]
    total: int
    page: int
    page_size: int


@router.get("/admin/api-logs", response_model=ApiLogsListResponse)
async def get_api_logs(
    admin_user_id: str = Depends(get_admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    method: Optional[str] = Query(None),
    path_contains: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None),
):
    """Get API request logs with pagination and filtering."""
    supabase = get_supabase_admin_client()

    # Build query
    query = supabase.table("api_request_logs").select("*", count="exact")

    # Apply filters
    if method:
        query = query.eq("method", method)
    if path_contains:
        query = query.ilike("path", f"%{path_contains}%")
    if status_code:
        query = query.eq("status_code", status_code)
    if user_id:
        query = query.eq("user_id", user_id)

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

    result = query.execute()

    logs = [
        ApiLogResponse(
            id=log.get("id", ""),
            user_id=log.get("user_id"),
            method=log.get("method", ""),
            path=log.get("path", ""),
            status_code=log.get("status_code"),
            response_time_ms=log.get("response_time_ms"),
            ip_address=log.get("ip_address"),
            error_message=log.get("error_message"),
            created_at=log.get("created_at", ""),
        )
        for log in (result.data or [])
    ]

    return ApiLogsListResponse(
        logs=logs,
        total=result.count or 0,
        page=page,
        page_size=page_size,
    )


@router.delete("/admin/api-logs/cleanup")
async def cleanup_api_logs(
    admin_user_id: str = Depends(get_admin_user),
    days_to_keep: int = Query(30, ge=1, le=365),
):
    """Delete API logs older than specified days."""
    from datetime import datetime, timedelta

    cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).isoformat()

    supabase = get_supabase_admin_client()

    result = (
        supabase.table("api_request_logs")
        .delete()
        .lt("created_at", cutoff_date)
        .execute()
    )

    deleted_count = len(result.data or [])

    return {
        "message": f"Deleted {deleted_count} logs older than {days_to_keep} days",
        "deleted_count": deleted_count,
    }


# ============================================
# Admin User Check Endpoint (for Frontend)
# ============================================


@router.get("/admin/check")
async def check_admin_status(
    authorization: Optional[str] = Header(None),
):
    """Check if current user has admin privileges.

    Returns is_admin status for the authenticated user.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return {"is_admin": False}

    token = authorization[7:]

    try:
        from src.clients.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        user = supabase.auth.get_user(token)

        if not user or not user.user:
            return {"is_admin": False}

        user_id = user.user.id

        admin_supabase = get_supabase_admin_client()
        result = (
            admin_supabase.table("user_settings")
            .select("is_admin")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        is_admin = result.data.get("is_admin", False) if result.data else False

        return {"is_admin": is_admin, "user_id": user_id}

    except Exception:
        return {"is_admin": False}
