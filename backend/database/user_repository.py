"""
Repository for User table operations
"""
import logging
from typing import Optional, List
from sqlalchemy import text
from models.user import User
from .base_repository import BaseRepository
from .connection import db_pool

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user operations"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text('SELECT * FROM "user" WHERE username = :username')
                result = conn.execute(query, {"username": username})
                row = result.fetchone()
                
                if row:
                    return User.model_validate(dict(row._mapping))
                return None
                
        except Exception as e:
            logger.error(f"[UserRepository] Get by username error: {e}", exc_info=True)
            raise
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text('SELECT * FROM "user" WHERE email = :email')
                result = conn.execute(query, {"email": email})
                row = result.fetchone()
                
                if row:
                    return User.model_validate(dict(row._mapping))
                return None
                
        except Exception as e:
            logger.error(f"[UserRepository] Get by email error: {e}", exc_info=True)
            raise
    
    def get_active_users(self) -> List[User]:
        """Get all active users"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text('SELECT * FROM "user" WHERE is_active = true ORDER BY created_at DESC')
                result = conn.execute(query)
                return [User.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[UserRepository] Get active users error: {e}", exc_info=True)
            raise
    
    def get_by_role(self, role: str) -> List[User]:
        """Get users by role"""
        try:
            with db_pool.get_connection_safe() as conn:
                query = text('SELECT * FROM "user" WHERE role = :role AND is_active = true')
                result = conn.execute(query, {"role": role})
                return [User.model_validate(dict(row._mapping)) for row in result]
                
        except Exception as e:
            logger.error(f"[UserRepository] Get by role error: {e}", exc_info=True)
            raise
    
    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user"""
        return self.update(user_id, {"is_active": False}, "user_id")
    
    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user"""
        return self.update(user_id, {"is_active": True}, "user_id")
    
    def get_or_create_user(self, email: str, username: str, google_id: str) -> User:
        """
        Get existing user by email or create a new user for Google OAuth.
        
        Args:
            email: User's email address
            username: User's display name
            google_id: Google OAuth ID (sub claim)
            
        Returns:
            User object (existing or newly created)
        """
        try:
            # Try to find existing user by email
            existing_user = self.get_by_email(email)
            
            if existing_user:
                # Update google_id if not set
                if not existing_user.google_id:
                    with db_pool.get_connection_safe() as conn:
                        query = text(
                            'UPDATE "user" SET google_id = :google_id WHERE user_id = :user_id RETURNING *'
                        )
                        result = conn.execute(query, {
                            "google_id": google_id,
                            "user_id": existing_user.user_id
                        })
                        conn.commit()
                        row = result.fetchone()
                        if row:
                            return User.model_validate(dict(row._mapping))
                
                logger.info(f"[UserRepository] Existing user found: {email}")
                return existing_user
            
            # Try to find by google_id
            with db_pool.get_connection_safe() as conn:
                query = text('SELECT * FROM "user" WHERE google_id = :google_id')
                result = conn.execute(query, {"google_id": google_id})
                row = result.fetchone()
                
                if row:
                    logger.info(f"[UserRepository] User found by google_id: {google_id}")
                    return User.model_validate(dict(row._mapping))
            
            # Create new user
            from datetime import datetime
            user_data = {
                "username": username,
                "email": email,
                "google_id": google_id,
                "password_hash": None,  # OAuth users don't have passwords
                "role": "User",
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            new_user = self.create(user_data)
            logger.info(f"[UserRepository] New OAuth user created: {email}")
            return new_user
            
        except Exception as e:
            logger.error(f"[UserRepository] Get or create user error: {e}", exc_info=True)
            raise


# Singleton instance
user_repository = UserRepository()
