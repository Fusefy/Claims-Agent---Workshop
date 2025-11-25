# backend/routes/hitl_routes.py
"""
API routes for HITL (Human-in-the-Loop) queue management
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from database import hitl_repository, claim_repository, history_repository

router = APIRouter(prefix="/api/hitl", tags=["HITL Queue"])
logger = logging.getLogger(__name__)


@router.get("/pending")
def get_pending_queue(limit: int = Query(50, ge=1, le=200)):
    """Get all pending HITL items"""
    try:
        queue = hitl_repository.get_pending_queue(limit=limit)
        return {
            "pending_items": queue,
            "total": len(queue)
        }
    except Exception as e:
        logger.error(f"Error getting pending queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claim/{claim_id}")
def get_hitl_by_claim(claim_id: str):
    """Get HITL item for a specific claim"""
    try:
        hitl = hitl_repository.get_by_claim(claim_id)
        if not hitl:
            raise HTTPException(status_code=404, detail="HITL record not found for this claim")
        return hitl
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting HITL by claim: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
def get_user_assigned_hitl(
    user_id: int,
    status: Optional[str] = None
):
    """Get HITL items assigned to a specific user"""
    try:
        items = hitl_repository.get_assigned_to_user(user_id, status)
        return {
            "user_id": user_id,
            "status": status,
            "items": items,
            "total": len(items)
        }
    except Exception as e:
        logger.error(f"Error getting user assigned HITL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{queue_id}/assign")
def assign_hitl_to_reviewer(
    queue_id: int,
    user_id: int
):
    """Assign HITL item to a reviewer"""
    try:
        hitl = hitl_repository.assign_to_reviewer(queue_id, user_id)
        if not hitl:
            raise HTTPException(status_code=404, detail="HITL item not found")
        
        # Log to history
        history_repository.log_status_change(
            claim_id=hitl.claim_id,
            old_status="Pending Review",
            new_status="Under Review",
            changed_by=f"user_{user_id}",
            role="Reviewer",
            change_reason=f"Assigned to reviewer {user_id}"
        )
        
        return hitl
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning HITL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{queue_id}/complete")
def complete_hitl_review(
    queue_id: int,
    decision: str,
    comments: Optional[str] = None
):
    """Complete HITL review with decision"""
    try:
        # Get HITL item to get claim_id
        hitl = hitl_repository.get_by_id(queue_id, "queue_id")
        if not hitl:
            raise HTTPException(status_code=404, detail="HITL item not found")
        
        # Complete review
        completed_hitl = hitl_repository.complete_review(queue_id, decision, comments)
        
        # Update claim status based on decision
        if decision == "Approved":
            claim_repository.update_status(hitl.claim_id, "Approved", comments)
        elif decision == "Denied":
            claim_repository.update_status(hitl.claim_id, "Denied", comments)
        
        # Log to history
        history_repository.log_status_change(
            claim_id=hitl.claim_id,
            old_status="Under Review",
            new_status=decision,
            changed_by=f"user_{hitl.assigned_to}",
            role="Reviewer",
            change_reason=comments or f"Review completed with decision: {decision}"
        )
        
        return completed_hitl
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing HITL review: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/overview")
def get_hitl_statistics():
    """Get HITL queue statistics"""
    try:
        stats = hitl_repository.get_queue_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting HITL statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
