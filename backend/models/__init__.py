"""
Database models initialization
"""
from db.connection import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON


def utc_now():
    """获取当前 UTC 时间（timezone-aware）"""
    return datetime.now(timezone.utc)


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    settings = Column(JSON, default=dict)


class Conversation(Base):
    """Chat conversation model"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene = Column(String(50), default="daily")
    user_message = Column(Text, nullable=False)
    ai_message = Column(Text, nullable=False)
    corrections = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)


class Word(Base):
    """Vocabulary word model"""
    __tablename__ = "words"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False, unique=True)
    phonetic = Column(String(100))
    meaning = Column(Text)
    example_sentences = Column(JSON, default=list)
    audio_path = Column(String(200))
    added_at = Column(DateTime, default=utc_now)
    reviewed_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    memory_strength = Column(Float, default=1.0)
    next_review = Column(DateTime)


class Pronunciation(Base):
    """Pronunciation evaluation model"""
    __tablename__ = "pronunciations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sentence_id = Column(Integer, nullable=False)
    score = Column(Integer)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)


class Writing(Base):
    """Writing correction model"""
    __tablename__ = "writings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text)
    corrections = Column(JSON, default=list)
    score = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)


class AISettings(Base):
    """AI configuration model"""
    __tablename__ = "ai_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), default="deepseek")  # deepseek, openai, ollama
    api_key = Column(String(200))
    model = Column(String(100), default="deepseek-chat")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1000)
    top_p = Column(Float, default=1.0)
    base_url = Column(String(200))  # For Ollama custom endpoint
    
    # TTS 配置
    tts_provider = Column(String(20), default="edge")  # edge, tencent
    tts_model = Column(String(50), default="en-US-AriaNeural")
    # 腾讯云 TTS 配置
    tencent_secret_id = Column(String(100))
    tencent_secret_key = Column(String(100))
    tencent_app_id = Column(String(50))
    
    # 发音评测配置 (Whisper)
    whisper_provider = Column(String(20), default="faster-whisper")  # faster-whisper, openai, tencent
    whisper_model = Column(String(20), default="base")  # tiny, base, small, medium
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class Statistics(Base):
    """Learning statistics model"""
    __tablename__ = "statistics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(20), unique=True, nullable=False)
    chat_count = Column(Integer, default=0)
    chat_minutes = Column(Integer, default=0)
    pronunciation_count = Column(Integer, default=0)
    pronunciation_avg_score = Column(Float, default=0)
    writing_count = Column(Integer, default=0)
    word_learned = Column(Integer, default=0)
    word_reviewed = Column(Integer, default=0)
    listening_minutes = Column(Integer, default=0)
    grammar_learned = Column(Integer, default=0)
    grammar_exercises = Column(Integer, default=0)