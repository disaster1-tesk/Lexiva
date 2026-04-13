"""
Statistics API - Learning Statistics
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
from db.connection import get_db
from models import Word, Conversation, Pronunciation, Writing, Statistics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/statistics", tags=["Statistics"])


def get_or_create_today_stats(session):
    """获取或创建今天的统计数据记录"""
    today = datetime.now().strftime("%Y-%m-%d")
    stats = session.query(Statistics).filter(Statistics.date == today).first()
    
    if not stats:
        stats = Statistics(
            date=today,
            chat_count=0,
            chat_minutes=0,
            pronunciation_count=0,
            pronunciation_avg_score=0,
            writing_count=0,
            word_learned=0,
            word_reviewed=0,
            listening_minutes=0
        )
        session.add(stats)
        session.commit()
        session.refresh(stats)
    
    return stats


@router.get("/summary")
async def get_summary():
    """Get learning statistics summary - 真实数据"""
    logger.info("Get statistics summary")
    
    session = next(get_db())
    try:
        # 获取所有统计数据
        all_stats = session.query(Statistics).all()
        
        total_words = session.query(Word).count()
        total_conversations = session.query(Conversation).count()
        total_writings = session.query(Writing).count()
        total_pronunciations = session.query(Pronunciation).count()
        total_listening = sum(s.listening_minutes for s in all_stats)
        
        # 计算连续学习天数
        # 从今天开始往前检查，只要有活动就继续，断了就停止
        streak_days = 0
        today = datetime.now()
        for i in range(365):
            check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            day_stat = session.query(Statistics).filter(Statistics.date == check_date).first()
            has_activity = day_stat and (day_stat.chat_count > 0 or day_stat.pronunciation_count > 0 or 
                        day_stat.writing_count > 0 or day_stat.word_reviewed > 0 or 
                        day_stat.listening_minutes > 0)
            
            if has_activity:
                streak_days += 1
            elif i > 0:  # 今天没有活动不算断 streak，往前找才断
                break
        
        logger.info(f"Statistics summary: words={total_words}, conversations={total_conversations}, streak={streak_days}")
        
        return {
            "code": 0,
            "data": {
                "total_words": total_words,
                "total_conversations": total_conversations,
                "total_writings": total_writings,
                "total_pronunciations": total_pronunciations,
                "total_listening": total_listening,
                "streak_days": streak_days,
                "total_grammar_learned": sum(s.grammar_learned for s in all_stats),
                "total_grammar_exercises": sum(s.grammar_exercises for s in all_stats),
                "chat_minutes": sum(s.chat_minutes for s in all_stats),
                "pronunciation_avg_score": sum(s.pronunciation_avg_score * s.pronunciation_count for s in all_stats) / total_pronunciations if total_pronunciations > 0 else 0
            }
        }
    finally:
        try:
            session.close()
        except Exception:
            pass


@router.get("/trend")
async def get_trend(days: int = 7):
    """Get learning trend - 真实数据"""
    logger.info(f"Get statistics trend: days={days}")
    
    session = next(get_db())
    try:
        trend = []
        today = datetime.now()
        
        for i in range(days):
            date = (today - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            day_stat = session.query(Statistics).filter(Statistics.date == date).first()
            
            if day_stat:
                trend.append({
                    "date": date,
                    "chat_count": day_stat.chat_count,
                    "words_reviewed": day_stat.word_reviewed,
                    "minutes": day_stat.chat_minutes + day_stat.listening_minutes
                })
            else:
                trend.append({
                    "date": date,
                    "chat_count": 0,
                    "words_reviewed": 0,
                    "minutes": 0
                })
        
        logger.info(f"Trend data generated: {len(trend)} days")
        
        return {"code": 0, "data": trend}
    finally:
        try:
            session.close()
        except Exception:
            pass


@router.post("/record")
async def record_activity(activity: dict):
    """Record learning activity - 持久化到数据库"""
    logger.info(f"Record activity: type={activity.get('type')}")
    
    session = next(get_db())
    try:
        activity_type = activity.get("type")
        data = activity.get("data", {})
        
        # 获取或创建今日统计
        stats = get_or_create_today_stats(session)
        
        if activity_type == "chat":
            stats.chat_count += 1
            stats.chat_minutes += data.get("minutes", 0)
        
        elif activity_type == "pronunciation":
            stats.pronunciation_count += 1
            old_avg = stats.pronunciation_avg_score
            old_count = stats.pronunciation_count - 1
            new_score = data.get("score", 0)
            # 更新平均分
            if old_count > 0:
                stats.pronunciation_avg_score = (old_avg * old_count + new_score) / stats.pronunciation_count
            else:
                stats.pronunciation_avg_score = new_score
        
        elif activity_type == "writing":
            stats.writing_count += 1
        
        elif activity_type == "word_added":
            stats.word_learned += 1
        
        elif activity_type == "word_reviewed":
            stats.word_reviewed += 1
        
        elif activity_type == "listening":
            stats.listening_minutes += data.get("minutes", 0)
        
        session.commit()
        
        logger.info(f"Activity recorded: {activity_type}")
        
        return {"code": 0, "message": "Activity recorded", "today_stats": {
            "chat_count": stats.chat_count,
            "pronunciation_count": stats.pronunciation_count,
            "writing_count": stats.writing_count,
            "word_reviewed": stats.word_reviewed
        }}
    except Exception as e:
        session.rollback()
        logger.error(f"Record activity error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            session.close()
        except Exception:
            pass