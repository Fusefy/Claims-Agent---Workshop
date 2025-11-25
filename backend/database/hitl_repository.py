"""
Repository for HitlQueue table operations
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from models.hitl_queue import HitlQueue
from .base_repository import BaseRepository
from .connection import db_pool

logger = logging.getLogger(__name__)


class HitlRepository(BaseRepository):
    """Repository for HITL queue operations"""
    
    def __init__(self):
        super().__init__(HitlQueue)
    
    def get_pending_queue(self, limit: int = 50) -> List[HitlQueue]:
        """Get all pending HITL items"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT * FROM hitlqueue
                    WHERE status = 'Pending'
                    ORDER BY created_at ASC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"limit": limit})
                return [HitlQueue.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[HitlRepository] Get pending queue error: {e}", exc_info=True)
            raise
    
    def get_by_claim(self, claim_id: str) -> Optional[HitlQueue]:
        """Get HITL item by claim ID"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT * FROM hitlqueue 
                    WHERE claim_id = :claim_id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                result = conn.execute(query, {"claim_id": claim_id})
                row = result.fetchone()
                
                if row:
                    return HitlQueue.model_validate(dict(row._mapping))
                return None
                
        except Exception as e:
            logger.error(f"[HitlRepository] Get by claim error: {e}", exc_info=True)
            raise
    
    def get_assigned_to_user(self, user_id: int, status: str = None) -> List[HitlQueue]:
        """Get HITL items assigned to a specific user"""
        try:
            with db_pool.get_connection_safe() as conn:
                if status:
                    query = text("""
                        SELECT * FROM hitlqueue
                        WHERE assigned_to = :user_id AND status = :status
                        ORDER BY created_at ASC
                    """)
                    result = conn.execute(query, {"user_id": user_id, "status": status})
                else:
                    query = text("""
                        SELECT * FROM hitlqueue
                        WHERE assigned_to = :user_id
                        ORDER BY created_at ASC
                    """)
                    result = conn.execute(query, {"user_id": user_id})
                
                return [HitlQueue.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[HitlRepository] Get assigned to user error: {e}", exc_info=True)
            raise
    
    def assign_to_reviewer(self, queue_id: int, user_id: int) -> Optional[HitlQueue]:
        """Assign HITL item to a reviewer"""
        return self.update(queue_id, {"assigned_to": user_id}, "queue_id")
    
    def complete_review(self, queue_id: int, decision: str, comments: str = None) -> Optional[HitlQueue]:
        """Complete a HITL review"""
        updates = {
            "status": "Completed",
            "decision": decision,
            "reviewed_at": datetime.utcnow()
        }
        if comments:
            updates["reviewer_comments"] = comments
        
        return self.update(queue_id, updates, "queue_id")
    
    def get_queue_statistics(self) -> dict:
        """Get HITL queue statistics"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed,
                        COUNT(CASE WHEN assigned_to IS NOT NULL THEN 1 END) as assigned
                    FROM hitlqueue
                """)
                result = conn.execute(query)
                row = result.fetchone()
                return dict(row._mapping)
                
        except Exception as e:
            logger.error(f"[HitlRepository] Get statistics error: {e}", exc_info=True)
            raise


# Singleton instance
hitl_repository = HitlRepository()
