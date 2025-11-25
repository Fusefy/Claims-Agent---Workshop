# backend/routes/claim_routes.py
"""
API routes for claim management using repositories
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging
from database import claim_repository, history_repository

router = APIRouter(prefix="/api/claims", tags=["Claims"])
logger = logging.getLogger(__name__)


@router.get("/{claim_id}")
def get_claim(claim_id: str):
    """Get a specific claim by ID"""
    try:
        claim = claim_repository.get_by_id(claim_id, "claim_id")
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        return claim
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_all_claims(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all claims with pagination"""
    try:
        claims = claim_repository.get_all(limit=limit, offset=offset)
        total = claim_repository.count()
        
        return {
            "claims": claims,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting claims: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{customer_id}")
def get_customer_claims(
    customer_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get all claims for a specific customer"""
    try:
        claims = claim_repository.get_by_customer(customer_id, limit=limit)
        return {
            "customer_id": customer_id,
            "claims": claims,
            "total": len(claims)
        }
    except Exception as e:
        logger.error(f"Error getting customer claims: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{status}")
def get_claims_by_status(
    status: str,
    limit: int = Query(100, ge=1, le=500)
):
    """Get claims by status"""
    try:
        claims = claim_repository.get_by_status(status, limit=limit)
        return {
            "status": status,
            "claims": claims,
            "total": len(claims)
        }
    except Exception as e:
        logger.error(f"Error getting claims by status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{claim_id}/status")
def update_claim_status(
    claim_id: str,
    new_status: str,
    notes: Optional[str] = None
):
    """Update claim status"""
    try:
        # Get old status for history
        old_claim = claim_repository.get_by_id(claim_id, "claim_id")
        if not old_claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Update status
        updated_claim = claim_repository.update_status(claim_id, new_status, notes)
        
        # Log to history
        history_repository.log_status_change(
            claim_id=claim_id,
            old_status=old_claim.claim_status,
            new_status=new_status,
            changed_by="api_user",
            role="User",
            change_reason=notes
        )
        
        return updated_claim
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating claim status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{claim_id}/history")
def get_claim_history(claim_id: str):
    """Get history for a specific claim"""
    try:
        history = history_repository.get_by_claim(claim_id)
        return {
            "claim_id": claim_id,
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting claim history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/overview")
def get_statistics():
    """Get claim statistics"""
    try:
        stats = claim_repository.get_statistics()
        # Map backend field names to frontend expected names
        return {
            "total": stats.get("total_claims", 0),
            "approved": stats.get("approved", 0),
            "pending": stats.get("pending", 0),
            "denied": stats.get("denied", 0),
            "withdrawn": stats.get("withdrawn", 0),
            "total_amount": stats.get("total_amount", 0),
            "approved_amount": stats.get("approved_amount", 0)
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
def search_claims(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500)
):
    """Search claims with multiple filters"""
    try:
        claims = claim_repository.search_claims(
            customer_id=customer_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return {
            "claims": claims,
            "total": len(claims),
            "filters": {
                "customer_id": customer_id,
                "status": status,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        logger.error(f"Error searching claims: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
