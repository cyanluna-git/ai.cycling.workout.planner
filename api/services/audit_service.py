"""Audit Logging Service.

Records all important system events to Supabase for admin monitoring.
"""

import os
from datetime import datetime
from typing import Optional, Any
from enum import Enum

from src.clients.supabase_client import get_supabase_admin_client


class AuditEventType(str, Enum):
    """Types of auditable events."""

    # Auth events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_SIGNUP = "user.signup"

    # API key events
    API_KEYS_UPDATED = "api_keys.updated"

    # Settings events
    SETTINGS_UPDATED = "settings.updated"

    # Workout events
    WORKOUT_GENERATED = "workout.generated"
    WORKOUT_SYNC_SUCCESS = "workout.sync_success"
    WORKOUT_SYNC_FAILED = "workout.sync_failed"

    # LLM events
    LLM_REQUEST = "llm.request"
    LLM_FALLBACK = "llm.fallback"
    LLM_ERROR = "llm.error"

    # System events
    ERROR = "error"


async def log_audit_event(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Log an audit event to Supabase.

    Args:
        event_type: Type of event to log.
        user_id: Optional user ID associated with the event.
        details: Optional additional details as JSON.
        ip_address: Optional client IP address.
    """
    try:
        supabase = get_supabase_admin_client()

        event_data = {
            "event_type": event_type.value,
            "user_id": user_id,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
        }

        supabase.table("audit_logs").insert(event_data).execute()

    except Exception as e:
        # Don't fail the main operation if audit logging fails
        print(f"[AUDIT] Failed to log event: {e}")


def log_audit_event_sync(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Synchronous version of audit logging (for non-async contexts)."""
    try:
        supabase = get_supabase_admin_client()

        event_data = {
            "event_type": event_type.value,
            "user_id": user_id,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
        }

        supabase.table("audit_logs").insert(event_data).execute()

    except Exception as e:
        print(f"[AUDIT] Failed to log event: {e}")
