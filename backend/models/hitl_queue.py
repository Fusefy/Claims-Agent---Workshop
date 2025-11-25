from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class HitlQueue(SQLModel, table=True):
    __tablename__ = "hitlqueue"  # Match SQL schema exactly
    
    queue_id: Optional[int] = Field(default=None, primary_key=True)
    claim_id: str = Field(foreign_key="proposedclaim.claim_id", max_length=50, nullable=False)
    status: str = Field(default='Pending', max_length=50)
    reviewer_comments: Optional[str] = Field(default=None)
    decision: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = Field(default=None)
