"""
Vocabulary API Routes
Word management endpoints
"""
import logging
import json
import re
import base64
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.connection import get_db
from models import Word

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vocabulary", tags=["Vocabulary"])


class ReviewRequest(BaseModel):
    word_id: int
    result: str  # "correct" or "incorrect"


class AddWordRequest(BaseModel):
    word: str


class VocabGenerateRequest(BaseModel):
    topic: str
    count: int = 10
    exclude_words: list[str] = []  # 排除的单词（用于继续生成）


class SpellCheckRequest(BaseModel):
    word: str
    answer: str


class PhoneticCheckRequest(BaseModel):
    word: str
    phonetic: str
    audio: str


class BatchAddWordsRequest(BaseModel):
    words: List[dict]  # [{"word": "...", "phonetic": "...", "meaning": "...", "type": "..."}]


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
        try:
            session.close()
        except Exception:
            pass


@router.post("/add")
async def add_word(request: AddWordRequest):
    """
    Add a new word
    """
    logger.info(f"Add word request: {request.word}")
    
    if not request.word.strip():
        logger.warning("Empty word received")
        raise HTTPException(status_code=400, detail="Word cannot be empty")
    
    word_text = request.word.strip().lower()
    
    session = next(get_db())
    try:
        # Check if already exists
        existing = session.query(Word).filter(Word.word == word_text).first()
        if existing:
            logger.info(f"Word already exists: {word_text}")
            return {"message": "Word already exists", "word": {
                "id": existing.id,
                "word": existing.word,
                "phonetic": existing.phonetic,
                "meaning": existing.meaning
            }}
        
        # Create new word
        word = Word(
            word=word_text,
            phonetic=f"/{word_text}/",
            meaning="",
            example_sentences=[],
            memory_strength=1.0,
            next_review=datetime.now() + timedelta(days=1)
        )
        session.add(word)
        session.commit()
        session.refresh(word)
        logger.info(f"Word added successfully: id={word.id}, word={word_text}")
        
        # 记录统计数据
        from models import Statistics
        today = datetime.now().strftime("%Y-%m-%d")
        stats = session.query(Statistics).filter(Statistics.date == today).first()
        if not stats:
            stats = Statistics(date=today)
            session.add(stats)
            session.flush()
        stats.word_learned += 1
        
        session.commit()
        
        return {
            "message": "Word added",
            "word": {
                "id": word.id,
                "word": word.word,
                "phonetic": word.phonetic,
                "meaning": word.meaning
            }
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add word: {str(e)}")
    finally:
        try:
            session.close()
        except Exception:
            pass


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
        try:
            session.close()
        except Exception:
            pass


@router.post("/review")
async def review_word(request: ReviewRequest):
    """
    Report review result for a word
    """
    logger.info(f"Review word request: word_id={request.word_id}, result={request.result}")
    
    session = next(get_db())
    try:
        word = session.query(Word).filter(Word.id == request.word_id).first()
        if not word:
            logger.warning(f"Word not found: word_id={request.word_id}")
            raise HTTPException(status_code=404, detail="Word not found")
        
        logger.info(f"Review update: word={word.word}, current_strength={word.memory_strength}")
        
        # 将前端传入的结果值映射为 correct/incorrect
        # 前端传入: "remember"(认识), "forgot"(不认识), "模糊"
        # 映射为: correct(答对), incorrect(答错)
        is_correct = request.result in ["correct", "remember"]
        
        # Update review counts
        word.reviewed_count += 1
        
        if is_correct:
            word.correct_count += 1
            # Strengthen memory
            word.memory_strength = min(5.0, word.memory_strength * 1.5)
            # Extend next review interval based on memory strength
            if word.memory_strength <= 1.0:
                days = 1
            elif word.memory_strength <= 1.5:
                days = 3
            elif word.memory_strength <= 2.5:
                days = 7
            elif word.memory_strength <= 3.5:
                days = 14
            elif word.memory_strength <= 4.5:
                days = 30
            else:
                days = 60
        else:
            # Weaken memory
            word.memory_strength = max(0.5, word.memory_strength * 0.5)
            days = 1
        
        word.next_review = datetime.now() + timedelta(days=days)
        session.commit()
        
        # 记录复习统计
        from models import Statistics
        today = datetime.now().strftime("%Y-%m-%d")
        stats = session.query(Statistics).filter(Statistics.date == today).first()
        if not stats:
            stats = Statistics(date=today)
            session.add(stats)
            session.flush()
        stats.word_reviewed += 1
        
        session.commit()
        
        return {
            "message": "Review saved",
            "memory_strength": word.memory_strength,
            "next_review": word.next_review.isoformat()
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save review: {str(e)}")
    finally:
        try:
            session.close()
        except Exception:
            pass


@router.get("/to-review")
async def get_words_to_review():
    """
    Get words due for review
    """
    session = next(get_db())
    try:
        now = datetime.now()
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
        try:
            session.close()
        except Exception:
            pass


@router.post("/generate")
async def generate_vocabulary(request: VocabGenerateRequest):
    """
    AI生成单词（支持继续生成，排除已默写过的单词）
    """
    from services.ai_chat import chat_service

    logger.info(f"Generate vocabulary: topic={request.topic}, count={request.count}, exclude={len(request.exclude_words)}")

    # 构建排除单词的提示
    exclude_hint = ""
    if request.exclude_words and len(request.exclude_words) > 0:
        exclude_hint = f"\n重要提示：请不要生成以下单词，这些已经默写过了：{', '.join(request.exclude_words)}。请生成{request.count}个与\"{request.topic}\"相关的、全新的、不同的高频英语单词。"

    prompt = f"""请生成{request.count}个与"{request.topic}"相关的英语单词。
{exclude_hint}

你必须严格遵循以下JSON格式返回数据，不要有任何额外内容：

[
  {{"word": "comprehensive", "phonetic": "/ˌkɒmprɪˈhensɪv/", "meaning": "adj. 全面的；综合的", "type": "形容词", "example": "A comprehensive review of the project was conducted."}}
]

关键要求：
1. 只返回这一行JSON数组，不要有任何前缀文字
2. 不要使用```json或```包裹
3. 每个单词必须包含：word(英文单词)、phonetic(IPA音标)、meaning(中文释义)、type(词性)、example(英文例句)
4. 音标必须使用IPA格式，如 /æbdəmən/、/kəmˈprihensɪv/
5. 返回{request.count}个不同的单词"""

    try:
        result = await chat_service.chat(prompt, scene="exam")
        reply = result.get("reply", "")

        # 清理回复内容，移除可能的markdown标记
        reply = reply.strip()
        reply = reply.replace('```json', '').replace('```', '').replace('```markdown', '')

        # 解析JSON - 尝试多种方式
        words = []
        
        # 方法1: 尝试直接解析
        try:
            words = json.loads(reply)
        except json.JSONDecodeError:
            pass
        
        # 方法2: 尝试正则提取JSON数组
        if not words:
            match = re.search(r'\[.*\]', reply, re.DOTALL)
            if match:
                try:
                    words = json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        
        # 方法3: 尝试找到所有可能的JSON对象
        if not words:
            # 尝试用正则提取每个单词对象
            obj_matches = re.findall(r'\{[^{}]*\}', reply)
            for obj_str in obj_matches:
                try:
                    obj = json.loads(obj_str)
                    if "word" in obj:
                        words.append(obj)
                except:
                    pass

        if not words:
            logger.warning(f"Failed to parse AI response as JSON: {reply[:200]}")
            raise HTTPException(status_code=500, detail="AI返回的数据格式不正确，请重试")

        # 确保返回的数据格式正确
        formatted_words = []
        for w in words:
            formatted_words.append({
                "word": w.get("word", ""),
                "phonetic": w.get("phonetic", ""),
                "meaning": w.get("meaning", ""),
                "type": w.get("type", "未分类"),
                "example": w.get("example", "")
            })

        logger.info(f"Generated {len(formatted_words)} words")

        return {
            "code": 0,
            "data": {
                "words": formatted_words
            }
        }
    except Exception as e:
        logger.error(f"Generate vocabulary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成单词失败: {str(e)}")


@router.post("/spell-check")
async def check_spelling(request: SpellCheckRequest):
    """
    检查拼写
    """
    logger.info(f"Spell check: word={request.word}, answer={request.answer}")

    correct = request.answer.lower().strip() == request.word.lower().strip()

    return {
        "code": 0,
        "data": {
            "correct": correct,
            "correct_answer": request.word,
            "your_answer": request.answer
        }
    }


@router.post("/phonetic-check")
async def check_phonetic(request: PhoneticCheckRequest):
    """
    音标跟读评测
    """
    logger.info(f"Phonetic check: word={request.word}")

    try:
        # 解码音频
        audio_data = base64.b64decode(request.audio)
    except Exception as e:
        logger.error(f"Failed to decode audio: {e}")
        return {"code": 1, "message": "音频解码失败"}

    # 使用Whisper转写
    from services.ai_whisper import whisper_service

    try:
        result = await whisper_service.transcribe(audio_data, language="en")
    except Exception as e:
        logger.error(f"Whisper transcribe error: {e}")
        return {"code": 1, "message": f"音频识别失败: {str(e)}"}

    if not result.get("success"):
        return {"code": 1, "message": result.get("error", "音频识别失败")}

    # 比对转写结果与目标单词
    recognized = result.get("text", "").lower().strip()
    target = request.word.lower().strip()

    # 计算相似度
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, recognized, target).ratio()
    score = int(similarity * 100)

    # 生成评语
    issues = []
    if score < 60:
        issues.append("发音不够清晰，建议多听原声")
    elif score < 80:
        issues.append("发音基本正确，注意细节")
    else:
        issues.append("发音很棒！")

    logger.info(f"Phonetic check result: score={score}, recognized={recognized}")

    return {
        "code": 0,
        "data": {
            "text": recognized,
            "score": score,
            "issues": issues,
            "target": target
        }
    }


@router.post("/batch-add")
async def batch_add_words(request: BatchAddWordsRequest):
    """
    批量添加单词到单词本
    """
    logger.info(f"Batch add words: count={len(request.words)}")

    if not request.words:
        raise HTTPException(status_code=400, detail="单词列表不能为空")

    session = next(get_db())
    added_count = 0
    skipped_count = 0
    results = []

    try:
        for word_data in request.words:
            word_text = word_data.get("word", "").strip().lower()
            if not word_text:
                skipped_count += 1
                continue

            # 检查是否已存在
            existing = session.query(Word).filter(Word.word == word_text).first()
            if existing:
                skipped_count += 1
                results.append({
                    "word": word_text,
                    "status": "skipped",
                    "message": "已存在"
                })
                continue

            # 创建新单词
            word = Word(
                word=word_text,
                phonetic=word_data.get("phonetic", f"/{word_text}/"),
                meaning=word_data.get("meaning", ""),
                example_sentences=[],
                memory_strength=1.0,
                next_review=datetime.now() + timedelta(days=1)
            )
            session.add(word)
            added_count += 1
            results.append({
                "word": word_text,
                "status": "added"
            })

        session.commit()

        logger.info(f"Batch add completed: added={added_count}, skipped={skipped_count}")

        return {
            "code": 0,
            "message": f"成功添加 {added_count} 个单词，跳过 {skipped_count} 个",
            "data": {
                "added": added_count,
                "skipped": skipped_count,
                "results": results
            }
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Batch add words error: {e}")
        raise HTTPException(status_code=500, detail=f"批量添加失败: {str(e)}")
    finally:
        try:
            session.close()
        except Exception:
            pass