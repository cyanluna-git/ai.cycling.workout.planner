"""Admin API Router.

Protected endpoints for admin/system monitoring.
Requires admin authentication via ADMIN_SECRET environment variable.
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query
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
