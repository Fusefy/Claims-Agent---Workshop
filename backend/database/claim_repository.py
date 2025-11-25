"""
Repository for ProposedClaim table operations
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import text
from models.proposed_claim import ProposedClaim
from .base_repository import BaseRepository
from .connection import db_pool

logger = logging.getLogger(__name__)


class ClaimRepository(BaseRepository):
    """Repository for claim operations"""
    
    def __init__(self):
        super().__init__(ProposedClaim)
    
    def get_by_customer(self, customer_id: str, limit: int = 50) -> List[ProposedClaim]:
        """Get all claims for a customer"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT * FROM proposedclaim
                    WHERE customer_id = :customer_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"customer_id": customer_id, "limit": limit})
                return [ProposedClaim.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[ClaimRepository] Get by customer error: {e}", exc_info=True)
            raise
    
    def get_by_status(self, status: str, limit: int = 100) -> List[ProposedClaim]:
        """Get claims by status"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT * FROM proposedclaim
                    WHERE claim_status = :status
                    ORDER BY created_at DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"status": status, "limit": limit})
                return [ProposedClaim.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[ClaimRepository] Get by status error: {e}", exc_info=True)
            raise
    
    def update_status(self, claim_id: str, new_status: str, notes: str = None) -> Optional[ProposedClaim]:
        """Update claim status (must be Approved, Pending, or Denied)"""
        # Validate status
        valid_statuses = ["Approved", "Pending", "Denied"]
        if new_status not in valid_statuses:
            logger.warning(f"[ClaimRepository] Invalid status '{new_status}', defaulting to 'Pending'")
            new_status = "Pending"
        
        updates = {
            "claim_status": new_status,
            "updated_at": datetime.utcnow()
        }
        if notes:
            updates["notes"] = notes
        
        return self.update(claim_id, updates, "claim_id")
    
    def update_guardrail_status(
        self, 
        claim_id: str, 
        guardrail_summary: dict = None
    ) -> Optional[ProposedClaim]:
        """Update guardrail validation summary"""
        updates = {
            "updated_at": datetime.utcnow()
        }
        if guardrail_summary:
            updates["guardrail_summary"] = guardrail_summary
        
        return self.update(claim_id, updates, "claim_id")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get claim statistics"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT 
                        COUNT(*) as total_claims,
                        COUNT(CASE WHEN claim_status = 'Approved' THEN 1 END) as approved,
                        COUNT(CASE WHEN claim_status = 'Denied' THEN 1 END) as denied,
                        COUNT(CASE WHEN claim_status = 'Pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN claim_status = 'Withdrawn' THEN 1 END) as withdrawn,
                        COALESCE(SUM(claim_amount), 0) as total_amount,
                        COALESCE(SUM(approved_amount), 0) as approved_amount
                    FROM proposedclaim
                """)
                result = conn.execute(query)
                row = result.fetchone()
                return dict(row._mapping)
                
        except Exception as e:
            logger.error(f"[ClaimRepository] Get statistics error: {e}", exc_info=True)
            raise
    
    def search_claims(
        self,
        customer_id: str = None,
        status: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[ProposedClaim]:
        """Search claims with multiple filters"""
        try:
            conditions = []
            params = {"limit": limit}
            
            if customer_id:
                conditions.append("customer_id = :customer_id")
                params["customer_id"] = customer_id
            
            if status:
                conditions.append("claim_status = :status")
                params["status"] = status
            
            if start_date:
                conditions.append("created_at >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                conditions.append("created_at <= :end_date")
                params["end_date"] = end_date
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            with db_pool.get_connection_safe() as conn:
                query = text(f"""
                    SELECT * FROM proposedclaim
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, params)
                return [ProposedClaim.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[ClaimRepository] Search claims error: {e}", exc_info=True)
            raise


# Singleton instance
claim_repository = ClaimRepository()
