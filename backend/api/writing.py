"""
Writing API Routes
Writing correction endpoints
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.writing import writing_service
from db.connection import get_db
from models import Writing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/writing", tags=["Writing"])

class WritingRequest(BaseModel):
    text: str
    exam_type: str = "general"


@router.post("/correct")
async def correct_writing(request: WritingRequest):
    """
    Correct writing text
    """
    logger.info(f"Writing correction request: text_len={len(request.text)}, exam_type={request.exam_type}")
    
    if not request.text.strip():
        logger.warning("Empty text received")
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        result = await writing_service.correct(request.text, request.exam_type)
        logger.info(f"Writing corrected: correction_count={len(result.get('corrections', []))}")
    except Exception as e:
        logger.error(f"Writing service error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Writing correction failed")
    
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
        logger.info(f"Writing saved: id={writing.id}")
    finally:
        try:
            session.close()
        except Exception:
            pass
    
    return result


@router.get("/history")
async def get_history(page: int = 1, limit: int = 20):
    """
    Get correction history
    """
    logger.info(f"Get writing history: page={page}, limit={limit}")
    
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
        
        logger.info(f"Writing history retrieved: count={len(writings)}, total={total}")
        
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
        try:
            session.close()
        except Exception:
            pass