"""
Vocabulary API Routes
Word management endpoints
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import get_db
from models import Word


# Request models
class AddWordRequest(BaseModel):
    word: str


class ReviewRequest(BaseModel):
    word_id: int
    result: str  # "correct" or "incorrect"


router = APIRouter(prefix="/api/vocabulary", tags=["Vocabulary"])


@router.get("/list")
async def get_words():
    """
    Get all vocabulary words
    """
    session = next(get_db())
    try:
        words = session.query(Word).order_by(Word.added_at.desc()).all()
        
        return {
            "items": [
                {
                    "id": w.id,
                    "word": w.word,
                    "phonetic": w.phonetic,
                    "meaning": w.meaning,
                    "example_sentences": w.example_sentences,
                    "added_at": w.added_at.isoformat() if w.added_at else None,
                    "reviewed_count": w.reviewed_count,
                    "correct_count": w.correct_count,
                    "memory_strength": w.memory_strength,
                    "next_review": w.next_review.isoformat() if w.next_review else None
                }
                for w in words
            ],
            "total": len(words)
        }
    finally:
        session.close()


@router.post("/add")
async def add_word(request: AddWordRequest):
    """
    Add a new word
    """
    if not request.word.strip():
        raise HTTPException(status_code=400, detail="Word cannot be empty")
    
    word_text = request.word.strip().lower()
    
    session = next(get_db())
    try:
        # Check if already exists
        existing = session.query(Word).filter(Word.word == word_text).first()
        if existing:
            return {"message": "Word already exists", "word": existing}
        
        # Create new word (simple version - could enhance with AI)
        word = Word(
            word=word_text,
            phonetic=f"/{word_text}/",
            meaning="",
            example_sentences=[],
            memory_strength=1.0,
            next_review=datetime.utcnow() + timedelta(days=1)
        )
        session.add(word)
        session.commit()
        session.refresh(word)
        
        return {
            "message": "Word added",
            "word": {
                "id": word.id,
                "word": word.word,
                "phonetic": word.phonetic,
                "meaning": word.meaning
            }
        }
    finally:
        session.close()


@router.delete("/{word_id}")
async def delete_word(word_id: int):
    """
    Delete a word
    """
    session = next(get_db())
    try:
        word = session.query(Word).filter(Word.id == word_id).first()
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")
        
        session.delete(word)
        session.commit()
        
        return {"message": "Word deleted"}
    finally:
        session.close()


@router.post("/review")
async def review_word(request: ReviewRequest):
    """
    Report review result for a word
    """
    session = next(get_db())
    try:
        word = session.query(Word).filter(Word.id == request.word_id).first()
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")
        
        # Update review counts
        word.reviewed_count += 1
        
        if request.result == "correct":
            word.correct_count += 1
            # Strengthen memory
            word.memory_strength = min(5.0, word.memory_strength * 1.5)
            # Extend next review interval
            intervals = {
                1.0: 1,   # 1 day
                1.5: 3,   # 3 days
                2.0: 7,   # 1 week
                3.0: 14,  # 2 weeks
                4.0: 30,  # 1 month
                5.0: 60   # 2 months
            }
            days = intervals.get(int(word.memory_strength), 7)
        else:
            # Weaken memory
            word.memory_strength = max(0.5, word.memory_strength * 0.5)
            days = 1
        
        word.next_review = datetime.utcnow() + timedelta(days=days)
        session.commit()
        
        return {
            "message": "Review saved",
            "memory_strength": word.memory_strength,
            "next_review": word.next_review.isoformat()
        }
    finally:
        session.close()


@router.get("/to-review")
async def get_words_to_review():
    """
    Get words due for review
    """
    session = next(get_db())
    try:
        now = datetime.utcnow()
        words = (
            session.query(Word)
            .filter(Word.next_review <= now)
            .order_by(Word.next_review)
            .limit(10)
            .all()
        )
        
        return {
            "items": [
                {
                    "id": w.id,
                    "word": w.word,
                    "phonetic": w.phonetic,
                    "meaning": w.meaning,
                    "memory_strength": w.memory_strength
                }
                for w in words
            ],
            "total": len(words)
        }
    finally:
        session.close()