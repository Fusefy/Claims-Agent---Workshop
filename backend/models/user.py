from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    __tablename__ = "user"  # Match SQL schema exactly
    
    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, max_length=100, nullable=False, unique=True)
    email: str = Field(index=True, max_length=150, nullable=False, unique=True)
    password_hash: Optional[str] = Field(default=None, nullable=True)  # Optional for OAuth users
    google_id: Optional[str] = Field(default=None, max_length=255, nullable=True, index=True)  # Google OAuth ID
    role: str = Field(default="User", max_length=20)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
