from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database.feedback_repository import FeedbackRepository

router = APIRouter()
feedback_repo = FeedbackRepository()

class FeedbackCreate(BaseModel):
    user_id: int
    risk_type: str
    severity: str
    title: str
    description: str

@router.post("/", response_model=dict)
async def create_feedback(feedback: FeedbackCreate):
    """
    Submit new risk feedback.
    """
    try:
        result = feedback_repo.create_feedback(feedback.dict())
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create feedback")
        
        return {
            "message": "Feedback submitted successfully",
            "data": result
        }
    except Exception as e:
        print(f"Error creating feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=dict)
async def get_all_feedback():
    """
    Get all feedback submissions (admin only - simplified for now).
    """
    try:
        results = feedback_repo.get_all_feedback()
        return {
            "data": results
        }
    except Exception as e:
        print(f"Error fetching feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
