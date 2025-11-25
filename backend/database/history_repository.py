"""
Repository for ClaimHistory table operations
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from models.claim_history import ClaimHistory
from .base_repository import BaseRepository
from .connection import db_pool

logger = logging.getLogger(__name__)


class HistoryRepository(BaseRepository):
    """Repository for claim history operations"""
    
    def __init__(self):
        super().__init__(ClaimHistory)
    
    def get_by_claim(self, claim_id: str, limit: int = 100) -> List[ClaimHistory]:
        """Get history for a specific claim"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT * FROM claimhistory
                    WHERE claim_id = :claim_id
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"claim_id": claim_id, "limit": limit})
                return [ClaimHistory.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[HistoryRepository] Get by claim error: {e}", exc_info=True)
            raise
    
    def log_status_change(
        self, 
        claim_id: str, 
        old_status: str, 
        new_status: str,
        changed_by: str = "system",
        role: str = "Agent",
        change_reason: str = None
    ) -> ClaimHistory:
        """Log a status change"""
        try:
            history = ClaimHistory(
                claim_id=claim_id,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by,
                role=role,
                change_reason=change_reason,
                timestamp=datetime.utcnow()
            )
            return self.create(history)
        except Exception as e:
            logger.error(f"[HistoryRepository] Log status change error: {e}", exc_info=True)
            raise
    
    def get_recent_history(self, days: int = 7, limit: int = 100) -> List[ClaimHistory]:
        """Get recent claim history"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT * FROM claimhistory
                    WHERE timestamp >= NOW() - INTERVAL :days DAY
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"days": days, "limit": limit})
                return [ClaimHistory.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[HistoryRepository] Get recent history error: {e}", exc_info=True)
            raise
    
    def get_by_user(self, changed_by: str, limit: int = 100) -> List[ClaimHistory]:
        """Get history by user who made changes"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT * FROM claimhistory
                    WHERE changed_by = :changed_by
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"changed_by": changed_by, "limit": limit})
                return [ClaimHistory.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[HistoryRepository] Get by user error: {e}", exc_info=True)
            raise


# Singleton instance
history_repository = HistoryRepository()
