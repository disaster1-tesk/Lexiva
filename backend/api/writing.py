"""
Writing API Routes
Writing correction endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.writing import writing_service
from db.connection import get_db
from models import Writing


# Request model
class WritingRequest(BaseModel):
    text: str
    exam_type: str = "general"


router = APIRouter(prefix="/api/writing", tags=["Writing"])


@router.post("/correct")
async def correct_writing(request: WritingRequest):
    """
    Correct writing text
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    result = await writing_service.correct(request.text, request.exam_type)
    
    # Save to database
    session = next(get_db())
    try:
        writing = Writing(
            original_text=result["original_text"],
            corrected_text=result["corrected_text"],
            corrections=result.get("corrections", []),
            score=result.get("score", {})
        )
        session.add(writing)
        session.commit()
    finally:
        session.close()
    
    return result


@router.get("/history")
async def get_history(page: int = 1, limit: int = 20):
    """
    Get correction history
    """
    session = next(get_db())
    try:
        offset = (page - 1) * limit
        writings = (
            session.query(Writing)
            .order_by(Writing.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        total = session.query(Writing).count()
        
        return {
            "items": [
                {
                    "id": w.id,
                    "original_text": w.original_text,
                    "corrected_text": w.corrected_text,
                    "score": w.score,
                    "created_at": w.created_at.isoformat()
                }
                for w in writings
            ],
            "total": total,
            "page": page,
            "limit": limit
        }
    finally:
        session.close()