"""
Statistics API - Learning Statistics
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/api/statistics", tags=["Statistics"])


@router.get("/summary")
async def get_summary():
    """Get learning statistics summary"""
    # Return mock data for now
    return {
        "code": 0,
        "data": {
            "total_words": 0,
            "total_conversations": 0,
            "total_writings": 0,
            "total_pronunciations": 0,
            "total_listening": 0,
            "streak_days": 0
        }
    }


@router.get("/trend")
async def get_trend(days: int = 7):
    """Get learning trend"""
    # Return mock data
    trend = []
    today = datetime.now()
    for i in range(days):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({
            "date": date,
            "chat_count": 0,
            "words_reviewed": 0,
            "minutes": 0
        })
    
    return {"code": 0, "data": trend}


@router.post("/record")
async def record_activity(activity: dict):
    """Record learning activity"""
    # This would update the database
    return {"code": 0, "message": "Activity recorded"}