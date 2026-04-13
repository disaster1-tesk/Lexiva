"""
Dictation API Routes
AI-powered dictation practice with theme-based word generation
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import get_db
from models import Word

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dictation", tags=["Dictation"])

# 预设主题及对应单词
THEME_WORDS = {
    "travel": ["airport", "flight", "hotel", "reservation", "luggage", "passport", "visa", "tourist", "destination", "itinerary", "boarding", "departure", "arrival", "customs", "currency"],
    "shopping": ["price", "discount", "sale", "receipt", "cash", "credit", "brand", "size", "fitting room", "receipt", "refund", "bargain", "expensive", "affordable", "quality"],
    "work": ["meeting", "deadline", "project", "schedule", "email", "conference", "presentation", "report", "colleague", "client", "manager", "office", "remote", "overtime", "promotion"],
    "daily": ["breakfast", "lunch", "dinner", "recipe", "grocery", "housework", "laundry", "exercise", "apartment", "neighbor", "community", "park", "gym", "pharmacy", "convenience"],
    "food": ["restaurant", "menu", "appetizer", "dessert", "beverage", "order", "tip", "reservation", "delicious", "spicy", "salty", "sweet", "sour", "bitter", "fresh"],
    "health": ["doctor", "hospital", "medicine", "symptom", "diagnosis", "treatment", "prescription", "health insurance", "fever", "cough", "headache", "allergy", "infection", "virus", "recovery"],
    "technology": ["computer", "software", "internet", "website", "application", "database", "password", "username", "update", "download", "upload", "folder", "file", "email", "screen"],
    "education": ["student", "teacher", "classroom", "homework", "exam", "grade", "subject", "textbook", "lecture", "semester", "major", "minor", "degree", "diploma", "research"]
}


class DictationRequest(BaseModel):
    theme: str
    word_count: int = 10
    modes: list[str] = ["en2zh", "zh2en", "spelling"]


class SubmitAnswerRequest(BaseModel):
    question_id: str
    answer: str
    mode: str  # "en2zh", "zh2en", "spelling"


@router.post("/generate")
async def generate_dictation(request: DictationRequest):
    """
    Generate dictation practice based on theme
    """
    logger.info(f"Generate dictation: theme={request.theme}, count={request.word_count}")
    
    theme = request.theme.lower()
    
    # 获取主题对应单词
    if theme in THEME_WORDS:
        words = THEME_WORDS[theme]
    else:
        # 尝试从数据库中获取相似主题的单词
        session = next(get_db())
        try:
            db_words = session.query(Word).filter(
                Word.word.like(f"%{theme}%")
            ).limit(20).all()
            words = [w.word for w in db_words]
            if not words:
                # 随机获取
                import random
                all_words = session.query(Word).all()
                words = [w.word for w in all_words]
                if len(words) > request.word_count:
                    words = random.sample(words, request.word_count)
        finally:
            try:
                session.close()
            except Exception:
                pass
    
    # 如果没有足够单词，填充默认
    if len(words) < request.word_count:
        all_default_words = []
        for w_list in THEME_WORDS.values():
            all_default_words.extend(w_list)
        words = list(set(words + all_default_words))[:request.word_count]
    
    # 打乱顺序并选取
    import random
    random.shuffle(words)
    selected_words = words[:request.word_count]
    
    # 生成题目
    questions = []
    modes = request.modes if request.modes else ["en2zh", "zh2en", "spelling"]
    
    for i, word in enumerate(selected_words):
        # 轮换模式
        mode = modes[i % len(modes)]
        
        if mode == "en2zh":
            # 英译中
            questions.append({
                "id": f"q_{i}",
                "word": word,
                "type": "en2zh",
                "question": f"请写出单词的中文含义: {word}",
                " phonetic": f"/{word}/"
            })
        elif mode == "zh2en":
            # 中译英
            # 需要查询数据库获取中文含义
            session = next(get_db())
            meaning = ""
            try:
                w = session.query(Word).filter(Word.word == word).first()
                if w:
                    meaning = w.meaning
            finally:
                try:
                    session.close()
                except Exception:
                    pass
            
            questions.append({
                "id": f"q_{i}",
                "type": "zh2en",
                "meaning": meaning if meaning else f"{word}的中文",
                "question": f"请写出对应的英文单词"
            })
        else:
            # 拼写
            questions.append({
                "id": f"q_{i}",
                "word": word,
                "type": "spelling",
                "question": f"请听发音并拼写单词",
                "phonetic": f"/{word}/"
            })
    
    return {
        "code": 0,
        "data": {
            "theme": request.theme,
            "questions": questions,
            "total": len(questions)
        }
    }


@router.post("/submit")
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit answer for a dictation question
    """
    logger.info(f"Submit answer: {request.question_id}, answer={request.answer}, mode={request.mode}")
    
    # 从 question_id 中提取单词
    word = request.question_id.replace("q_", "")
    
    # 获取正确答案
    correct = False
    correct_answer = ""
    explanation = ""
    
    # 从数据库获取正确答案
    session = next(get_db())
    try:
        db_word = session.query(Word).filter(Word.word == word).first()
        if db_word:
            correct_answer = db_word.word
            if request.mode == "en2zh" or request.mode == "spelling":
                correct = request.answer.lower().strip() == db_word.word.lower().strip()
                explanation = db_word.meaning or ""
            else:
                # zh2en 模式
                correct = request.answer.lower().strip() == db_word.word.lower().strip()
                explanation = db_word.meaning or ""
        else:
            # 使用预设单词
            correct_answer = word
            correct = request.answer.lower().strip() == word.lower().strip()
    finally:
        try:
            session.close()
        except Exception:
            pass
    
    # 更新词汇统计
    if correct:
        session = next(get_db())
        try:
            db_word = session.query(Word).filter(Word.word == word).first()
            if db_word:
                db_word.correct_count += 1
                db_word.memory_strength = min(5.0, db_word.memory_strength * 1.2)
                session.commit()
        except Exception as e:
            logger.error(f"Update word stats error: {e}")
        finally:
            try:
                session.close()
            except Exception:
                pass
    
    return {
        "code": 0,
        "data": {
            "correct": correct,
            "correct_answer": correct_answer,
            "explanation": explanation
        }
    }


@router.get("/themes")
async def get_themes():
    """
    Get available themes
    """
    themes = []
    for theme, words in THEME_WORDS.items():
        themes.append({
            "id": theme,
            "name": theme.capitalize(),
            "word_count": len(words)
        })
    
    return {
        "code": 0,
        "data": themes
    }