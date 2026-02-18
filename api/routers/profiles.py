"""Profiles API Router.

Admin endpoints for browsing, viewing, and deleting workout profiles.
Requires admin authentication via JWT token.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.routers.admin import get_admin_user
from api.services.workout_profile_service import WorkoutProfileService

logger = logging.getLogger(__name__)

router = APIRouter()

_profile_service = WorkoutProfileService()


@router.get("/profiles/stats")
async def get_profile_stats(
    admin_user_id: str = Depends(get_admin_user),
):
    """Get workout profile DB statistics."""
    return _profile_service.get_profile_stats()


@router.get("/profiles")
async def list_profiles(
    admin_user_id: str = Depends(get_admin_user),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    """List workout profiles with pagination and filtering.

    Returns items (without steps_json/zwo_xml) and total count.
    """
    return _profile_service.list_profiles(
        offset=offset,
        limit=limit,
        category=category,
        difficulty=difficulty,
        source=source,
        search=search,
        is_active=is_active,
    )


@router.get("/profiles/{profile_id}")
async def get_profile(
    profile_id: int,
    admin_user_id: str = Depends(get_admin_user),
):
    """Get a single profile with all 24 columns including steps_json."""
    profile = _profile_service.get_profile_by_id(profile_id)
    if not profile:
        # Also try inactive profiles for admin view
        try:
            import sqlite3
            conn = _profile_service._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workout_profiles WHERE id = ?", (profile_id,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                profile = dict(row)
                if profile.get("steps_json") and isinstance(profile["steps_json"], str):
                    profile["steps_json"] = json.loads(profile["steps_json"])
                if profile.get("coach_notes") and isinstance(profile["coach_notes"], str):
                    try:
                        profile["coach_notes"] = json.loads(profile["coach_notes"])
                    except json.JSONDecodeError:
                        pass
                if profile.get("tags") and isinstance(profile["tags"], str):
                    try:
                        profile["tags"] = json.loads(profile["tags"])
                    except json.JSONDecodeError:
                        pass
            else:
                raise HTTPException(status_code=404, detail="Profile not found")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=404, detail="Profile not found")

    # Parse JSON string fields if not already parsed
    if isinstance(profile.get("tags"), str):
        try:
            profile["tags"] = json.loads(profile["tags"])
        except json.JSONDecodeError:
            profile["tags"] = []
    if isinstance(profile.get("coach_notes"), str):
        try:
            profile["coach_notes"] = json.loads(profile["coach_notes"])
        except json.JSONDecodeError:
            pass

    return profile


@router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: int,
    admin_user_id: str = Depends(get_admin_user),
):
    """Delete a workout profile (hard delete)."""
    deleted = _profile_service.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": f"Profile {profile_id} deleted", "id": profile_id}
