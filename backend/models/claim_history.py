from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class ClaimHistory(SQLModel, table=True):
    __tablename__ = "claimhistory"  # Match SQL schema exactly
    
    history_id: Optional[int] = Field(default=None, primary_key=True)
    claim_id: str = Field(foreign_key="proposedclaim.claim_id", max_length=50, nullable=False)
    old_status: Optional[str] = Field(default=None, max_length=50)
    new_status: Optional[str] = Field(default=None, max_length=50)
    changed_by: Optional[str] = Field(default=None, max_length=100)
    role: Optional[str] = Field(default=None, max_length=20)
    change_reason: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
