from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository
from models.feedback import Feedback
from sqlalchemy import text
from .connection import db_pool

class FeedbackRepository(BaseRepository):
    def __init__(self):
        super().__init__(Feedback)

    def create_feedback(self, feedback_data: Dict[str, Any]) -> Feedback:
        """
        Creates a new feedback record.
        """
        # Use the BaseRepository's create method which handles model validation and insertion
        return self.create(feedback_data)

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """
        Retrieves all feedback records with user details.
        """
        try:
            with db_pool.get_connection_safe() as conn:
                query = text("""
                    SELECT f.*, u.username, u.email 
                    FROM feedback f
                    JOIN "user" u ON f.user_id = u.user_id
                    ORDER BY f.created_at DESC
                """)
                result = conn.execute(query)
                
                # Convert rows to dicts
                return [dict(row._mapping) for row in result]
                
        except Exception as e:
            # Log the error (BaseRepository has a logger but it's not an instance attribute, 
            # so we'd need to import logging or just re-raise)
            print(f"[FeedbackRepository] Get all error: {e}")
            raise
