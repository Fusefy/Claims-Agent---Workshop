from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

class ProposedClaim(SQLModel, table=True):
    __tablename__ = "proposedclaim"  # Match SQL schema exactly
    
    claim_id: str = Field(primary_key=True, max_length=50)
    claim_name: Optional[str] = Field(default=None, max_length=200)  # Short descriptive name
    customer_id: str = Field(max_length=50, nullable=False)
    policy_id: Optional[str] = Field(default=None, max_length=50)
    claim_type: Optional[str] = Field(default=None, max_length=50)
    network_status: Optional[str] = Field(default=None, max_length=50)
    date_of_service: Optional[datetime] = Field(default=None)
    claim_amount: Optional[float] = Field(default=None)
    approved_amount: float = Field(default=0.0)
    claim_status: str = Field(default='Pending', max_length=50)
    error_type: Optional[str] = Field(default=None, max_length=100)
    ai_reasoning: Optional[str] = Field(default=None)  # AI explanation for status
    payment_status: str = Field(default='Pending', max_length=50)
    guardrail_summary: Optional[dict] = Field(
        default_factory=dict,
        sa_column=Column(MutableDict.as_mutable(JSONB))
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
