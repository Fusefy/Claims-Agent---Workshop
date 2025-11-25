# backend/routes/user_routes.py
"""
API routes for user management
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from database import user_repository

router = APIRouter(prefix="/api/users", tags=["Users"])
logger = logging.getLogger(__name__)


@router.get("/{user_id}")
def get_user(user_id: int):
    """Get a specific user by ID"""
    try:
        user = user_repository.get_by_id(user_id, "user_id")
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/username/{username}")
def get_user_by_username(username: str):
    """Get user by username"""
    try:
        user = user_repository.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by username: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_active_users():
    """Get all active users"""
    try:
        users = user_repository.get_active_users()
        return {
            "users": users,
            "total": len(users)
        }
    except Exception as e:
        logger.error(f"Error getting active users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/role/{role}")
def get_users_by_role(role: str):
    """Get users by role"""
    try:
        users = user_repository.get_by_role(role)
        return {
            "role": role,
            "users": users,
            "total": len(users)
        }
    except Exception as e:
        logger.error(f"Error getting users by role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/deactivate")
def deactivate_user(user_id: int):
    """Deactivate a user"""
    try:
        user = user_repository.deactivate_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/activate")
def activate_user(user_id: int):
    """Activate a user"""
    try:
        user = user_repository.activate_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
