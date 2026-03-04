"""Intervals.icu Webhook receiver.

Receives webhook events from Intervals.icu when athlete data changes
(activities, wellness, calendar). Invalidates TTL cache so the next
API request returns fresh data.

Webhook is configured once in the Intervals.icu OAuth app management UI.
All authorized athletes' events arrive at this single endpoint.

Verification: Intervals.icu sends the configured "Webhook Authorization Header"
value as the HTTP Authorization header with each POST. We compare this against
INTERVALS_WEBHOOK_SECRET env var.

Payload format (from Intervals.icu):
    {
        "events": [
            {
                "athlete_id": "i154786",
                "type": "ACTIVITY_UPLOADED",
                "timestamp": "2024-12-06T06:40:47.011+00:00",
                ...
            }
        ]
    }
"""

import logging
import os
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from api.services.cache_service import clear_user_cache
from api.services.user_api_service import get_user_id_by_athlete_id

logger = logging.getLogger(__name__)
router = APIRouter()

INTERVALS_WEBHOOK_SECRET = os.getenv("INTERVALS_WEBHOOK_SECRET")

# Event type → cache keys to invalidate
# None means clear entire user cache
EVENT_CACHE_MAP: dict[str, list[str] | None] = {
    "ACTIVITY_UPLOADED": None,  # Affects fitness/training/activities/calendar
    "ACTIVITY_ANALYZED": None,  # TSS recalculated, affects everything
    "WELLNESS_UPDATED": ["fitness:complete", "fitness:wellness"],
    "CALENDAR_UPDATED": ["calendar"],
}


class WebhookEvent(BaseModel):
    """Single event in the Intervals.icu webhook payload."""

    athlete_id: str
    type: str
    timestamp: str | None = None
    # Allow extra fields (activity details, etc.)
    model_config = {"extra": "allow"}


class WebhookPayload(BaseModel):
    """Intervals.icu webhook payload."""

    events: list[WebhookEvent]
    # Allow extra fields (secret body field, etc.) for forward-compatibility
    model_config = {"extra": "allow"}


@router.post("/webhooks/intervals")
async def receive_intervals_webhook(request: Request) -> dict[str, str]:
    """Receive webhook events from Intervals.icu.

    - Verifies Authorization header against INTERVALS_WEBHOOK_SECRET env var.
    - For each event, looks up the user by athlete_id and clears relevant cache.
    - Always returns 200 to prevent Intervals.icu from retrying.
    """
    # Check if webhook secret is configured
    if not INTERVALS_WEBHOOK_SECRET:
        logger.warning("INTERVALS_WEBHOOK_SECRET not configured, rejecting webhook")
        return Response(
            content='{"error": "webhook not configured"}',
            status_code=503,
            media_type="application/json",
        )

    # Verify Authorization header (set in Intervals.icu "Webhook Authorization Header")
    auth_header = request.headers.get("Authorization", "")
    if auth_header != INTERVALS_WEBHOOK_SECRET:
        logger.warning("Webhook Authorization header mismatch — rejecting request")
        return Response(
            content='{"error": "invalid secret"}',
            status_code=403,
            media_type="application/json",
        )

    # Parse payload — return 200 even on parse errors to prevent retries
    try:
        body = await request.json()
        payload = WebhookPayload(**body)
    except Exception as e:
        logger.warning(f"Webhook payload parse error: {e}")
        return {"status": "ok"}

    # Process events
    processed = 0
    for event in payload.events:
        cache_keys = EVENT_CACHE_MAP.get(event.type)

        if event.type not in EVENT_CACHE_MAP:
            logger.debug(f"Ignoring unsupported webhook event type: {event.type}")
            continue

        # Look up user_id from athlete_id
        user_id = await get_user_id_by_athlete_id(event.athlete_id)
        if not user_id:
            logger.debug(
                f"No user found for athlete_id {event.athlete_id}, skipping"
            )
            continue

        # Clear cache
        clear_user_cache(user_id, keys=cache_keys)
        processed += 1
        logger.info(
            f"Webhook: {event.type} for athlete {event.athlete_id} "
            f"→ cache invalidated (user {user_id[:8]}..., "
            f"keys={cache_keys or 'ALL'})"
        )

    logger.info(f"Webhook processed: {processed}/{len(payload.events)} events")
    return {"status": "ok"}
