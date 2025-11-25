from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class Feedback(SQLModel, table=True):
    feedback_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    risk_type: str = Field(index=True)
    severity: str
    title: str
    description: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
