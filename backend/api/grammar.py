"""
Grammar API Routes
AI-powered grammar learning with explanations, examples, and exercises
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/grammar", tags=["Grammar"])

# 语法点分类和数据
GRAMMAR_TOPICS = {
    "tenses": {
        "name": "时态",
        "topics": [
            {
                "id": "present_simple",
                "name": "一般现在时",
                "description": "描述习惯性动作、普遍真理和当前状态",
                "formula": "主语 + 动词原形（第三人称单数加s/es）",
                "examples": [
                    "I drink coffee every morning.",
                    "She works in a bank.",
                    "The sun rises in the east."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "He ___ (play) football every weekend.",
                        "answer": "plays",
                        "options": ["play", "plays", "playing", "played"]
                    },
                    {
                        "type": "choice",
                        "question": "Water ___ (boil) at 100°C.",
                        "answer": "boils",
                        "options": ["boil", "boils", "boiling", "boiled"]
                    },
                    {
                        "type": "rewrite",
                        "question": "She watching TV every night. (纠正句子)",
                        "answer": "She watches TV every night.",
                        "explanation": "第三人称单数动词需要加s"
                    }
                ]
            },
            {
                "id": "past_simple",
                "name": "一般过去时",
                "description": "描述过去完成的动作或状态",
                "formula": "主语 + 动词过去式",
                "examples": [
                    "I visited Paris last year.",
                    "She bought a new car yesterday.",
                    "They finished the project on time."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "We ___ (go) to the beach yesterday.",
                        "answer": "went",
                        "options": ["go", "went", "going", "goes"]
                    },
                    {
                        "type": "choice",
                        "question": "She ___ (eat) breakfast at 7am.",
                        "answer": "ate",
                        "options": ["eat", "ate", "eating", "eaten"]
                    }
                ]
            },
            {
                "id": "present_perfect",
                "name": "现在完成时",
                "description": "描述过去发生但与现在有关联的动作",
                "formula": "主语 + have/has + 过去分词",
                "examples": [
                    "I have finished my homework.",
                    "She has lived here for five years.",
                    "They have already left."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "I ___ (read) three books this month.",
                        "answer": "have read",
                        "options": ["read", "have read", "am reading", "was reading"]
                    }
                ]
            }
        ]
    },
    "parts_of_speech": {
        "name": "词性",
        "topics": [
            {
                "id": "noun",
                "name": "名词",
                "description": "表示人、事物、地点或抽象概念",
                "formula": "可数名词 / 不可数名词",
                "examples": [
                    "The cat is sleeping on the bed.",
                    "I have a lot of homework to do.",
                    "Honesty is the best policy."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Which word is a noun?",
                        "answer": "happiness",
                        "options": ["quickly", "happiness", "beautiful", "run"]
                    },
                    {
                        "type": "fill_blank",
                        "question": "She bought a new ___ (book).",
                        "answer": "book",
                        "options": ["book", "books", "book's", "booked"]
                    }
                ]
            },
            {
                "id": "verb",
                "name": "动词",
                "description": "表示动作或状态",
                "formula": "行为动词 / 系动词 / 助动词 / 情态动词",
                "examples": [
                    "She runs very fast.",
                    "He is a teacher.",
                    "I can speak English."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Which is a linking verb?",
                        "answer": "become",
                        "options": ["run", "eat", "become", "see"]
                    }
                ]
            },
            {
                "id": "adjective",
                "name": "形容词",
                "description": "描述名词的特征或性质",
                "formula": "形容词 + 名词 / be + 形容词",
                "examples": [
                    "She has a beautiful smile.",
                    "The book is interesting.",
                    "He is taller than his brother."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "This is an ___ (interest) book.",
                        "answer": "interesting",
                        "options": ["interest", "interesting", "interested", "interests"]
                    }
                ]
            },
            {
                "id": "adverb",
                "name": "副词",
                "description": "修饰动词、形容词或其他副词",
                "formula": "方式副词 / 时间副词 / 地点副词 / 程度副词",
                "examples": [
                    "She speaks English very well.",
                    "He arrived early.",
                    "They live here."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Choose the adverb: She sings ___ (beautiful).",
                        "answer": "beautifully",
                        "options": ["beautiful", "beautifully", "beauty", "beautifuly"]
                    }
                ]
            },
            {
                "id": "preposition",
                "name": "介词",
                "description": "表示名词或代词与其他词的关系",
                "formula": "介词 + 名词/代词",
                "examples": [
                    "The cat is under the table.",
                    "I go to school by bus.",
                    "She is interested in music."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "She sits ___ the window.",
                        "answer": "by",
                        "options": ["in", "on", "at", "by"]
                    }
                ]
            },
            {
                "id": "conjunction",
                "name": "连词",
                "description": "连接词、短语或句子",
                "formula": "并列连词 / 从属连词",
                "examples": [
                    "I like tea and coffee.",
                    "Because it rained, we stayed home.",
                    "You can either go or stay."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Choose the conjunction: I will go ___ it stops raining.",
                        "answer": "when",
                        "options": ["and", "but", "when", "or"]
                    }
                ]
            }
        ]
    },
    "clauses": {
        "name": "从句",
        "topics": [
            {
                "id": "that_clause",
                "name": "that 从句",
                "description": "用作主语、宾语、表语的从句",
                "examples": [
                    "I think that he is right.",
                    "That she passed the exam surprised us.",
                    "The problem is that we have no time."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "I believe ___ he will come.",
                        "answer": "that",
                        "options": ["that", "which", "what", "where"]
                    }
                ]
            },
            {
                "id": "conditional",
                "name": "条件句",
                "description": "表达假设和条件",
                "formula": "If + 现在时态, 主语 + will/would + 动词",
                "examples": [
                    "If it rains, I will stay home.",
                    "If you work hard, you will succeed.",
                    "If I were you, I would apologize."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "If she ___ (be) late, we will start without her.",
                        "answer": "is",
                        "options": ["is", "was", "will be", "are"]
                    }
                ]
            },
            {
                "id": "relative_clause",
                "name": "定语从句",
                "description": "修饰名词或代词的从句",
                "formula": "名词/代词 + 关系词 + 从句",
                "examples": [
                    "The book that I bought is interesting.",
                    "The girl who is playing piano is my sister.",
                    "This is the place where we met."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Choose the correct relative pronoun: I know the man ___ helped me.",
                        "answer": "who",
                        "options": ["who", "which", "where", "when"]
                    }
                ]
            }
        ]
    },
    "sentence_patterns": {
        "name": "句型",
        "topics": [
            {
                "id": "simple_sentence",
                "name": "简单句",
                "description": "只有一个主语和一个谓语的句子",
                "formula": "主语 + 谓语",
                "examples": [
                    "The sun rises.",
                    "She sings beautifully.",
                    "They are students."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Which is a simple sentence?",
                        "answer": "I like music.",
                        "options": ["I like music.", "I like music and she likes dance.", "Because it rained, we stayed home.", "If you study hard, you will pass."]
                    }
                ]
            },
            {
                "id": "compound_sentence",
                "name": "并列句",
                "description": "用并列连词连接的两个简单句",
                "formula": "简单句 + 并列连词 + 简单句",
                "examples": [
                    "I wanted to go, but it was raining.",
                    "She sings and he plays piano.",
                    "You can either study or play."
                ],
                "exercises": [
                    {
                        "type": "rewrite",
                        "question": "Combine: It was late. We kept working. (用and连接)",
                        "answer": "It was late and we kept working.",
                        "explanation": "用and连接两个并列分句"
                    }
                ]
            },
            {
                "id": "complex_sentence",
                "name": "复合句",
                "description": "包含主句和从句的句子",
                "formula": "主句 + 从句 / 从句 + 主句",
                "examples": [
                    "When I arrived, she was cooking.",
                    "I know that he is honest.",
                    "If you work hard, you will succeed."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Which is a complex sentence?",
                        "answer": "Because I was tired, I went to bed early.",
                        "options": ["I like tea and coffee.", "Because I was tired, I went to bed early.", "He sings but she dances.", "It was raining; we stayed home."]
                    }
                ]
            },
            {
                "id": "passive_voice_sentence",
                "name": "被动语态句",
                "description": "主语是动作接受者的句子",
                "formula": "主语 + be + 过去分词",
                "examples": [
                    "The book was written by Mark Twain.",
                    "The window is broken.",
                    "English is spoken worldwide."
                ],
                "exercises": [
                    {
                        "type": "rewrite",
                        "question": "They built the house in 2020. (改为被动)",
                        "answer": "The house was built in 2020.",
                        "explanation": "过去时的被动：was/were + 过去分词"
                    }
                ]
            },
            {
                "id": "there_be_sentence",
                "name": "There be 句型",
                "description": "表示某地存在某物",
                "formula": "There + be + 主语 + 地点",
                "examples": [
                    "There is a book on the table.",
                    "There are some students in the classroom.",
                    "There was a meeting yesterday."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "___ a lot of people in the park.",
                        "answer": "There are",
                        "options": ["There is", "There are", "There was", "There be"]
                    }
                ]
            }
        ]
    },
    "nonfinite": {
        "name": "非谓语",
        "topics": [
            {
                "id": "gerund",
                "name": "动名词",
                "description": "动词+ing，用作主语、表语、宾语",
                "examples": [
                    "Swimming is good for health.",
                    "I enjoy reading novels.",
                    "Her job is teaching English."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "I like ___ (play) basketball.",
                        "answer": "playing",
                        "options": ["play", "plays", "playing", "played"]
                    }
                ]
            },
            {
                "id": "infinitive",
                "name": "不定式",
                "description": "to + 动词原形，用作主语、宾语、表语、目的",
                "examples": [
                    "To err is human.",
                    "I want to learn English.",
                    "She came to help us."
                ],
                "exercises": [
                    {
                        "type": "fill_blank",
                        "question": "I want ___ (go) shopping.",
                        "answer": "to go",
                        "options": ["go", "to go", "going", "goes"]
                    }
                ]
            },
            {
                "id": "participle",
                "name": "分词",
                "description": "现在分词和过去分词，用作定语、表语、状语",
                "examples": [
                    "The running boy is my brother.",
                    "The broken cup is on the table.",
                    "Hearing the news, she felt happy."
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Which is a past participle?",
                        "answer": "broken",
                        "options": ["breaking", "broken", "break", "breaks"]
                    }
                ]
            }
        ]
    },
    "voice": {
        "name": "语态",
        "topics": [
            {
                "id": "passive_voice",
                "name": "被动语态",
                "description": "主语是动作的接受者",
                "formula": "主语 + be + 过去分词",
                "examples": [
                    "The book was written by Mark Twain.",
                    "The window is broken.",
                    "English is spoken worldwide."
                ],
                "exercises": [
                    {
                        "type": "rewrite",
                        "question": "They built the house in 2020. (改为被动)",
                        "answer": "The house was built in 2020.",
                        "explanation": "过去时的被动：was/were + 过去分词"
                    },
                    {
                        "type": "fill_blank",
                        "question": "The song ___ (sing) by many people.",
                        "answer": "is sung",
                        "options": ["is sing", "is sung", "sings", "singing"]
                    }
                ]
            }
        ]
    },
    "word_formation": {
        "name": "构词法",
        "topics": [
            {
                "id": "derivation",
                "name": "派生法",
                "description": "通过添加前缀或后缀构成新词",
                "formula": "前缀 + 词根 / 词根 + 后缀",
                "examples": [
                    "unhappy (un- + happy)",
                    "teacher (teach + -er)",
                    "impossible (im- + possible)"
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Which is the suffix in 'beautiful'?",
                        "answer": "-ful",
                        "options": ["beau-", "-ful", "beauti", "-iful"]
                    }
                ]
            },
            {
                "id": "compound",
                "name": "合成法",
                "description": "两个或多个词合成一个新词",
                "formula": "词 + 词 = 新词",
                "examples": [
                    "water + bottle = waterbottle",
                    "sun + flower = sunflower",
                    "class + room = classroom"
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "Which is a compound word?",
                        "answer": "bedroom",
                        "options": ["bedroom", "beautiful", "together", "understand"]
                    }
                ]
            },
            {
                "id": "conversion",
                "name": "转化法",
                "description": "词性转换，拼写不变",
                "formula": "名词 → 动词 / 动词 → 名词",
                "examples": [
                    "water (n.) → water (v.)",
                    "book (n.) → book (v.)",
                    "work (n.) → work (v.)"
                ],
                "exercises": [
                    {
                        "type": "choice",
                        "question": "'Run' can be both a verb and a noun. This is called ___.",
                        "answer": "conversion",
                        "options": ["conversion", "derivation", "compound", "prefix"]
                    }
                ]
            }
        ]
    }
}


class GrammarLearnRequest(BaseModel):
    topic_id: str


class GrammarExerciseRequest(BaseModel):
    topic_id: str
    exercise_id: int
    answer: str


@router.get("/topics")
async def get_grammar_topics():
    """
    Get all grammar topics
    """
    topics = []
    for category_id, category in GRAMMAR_TOPICS.items():
        topics.append({
            "id": category_id,
            "name": category["name"],
            "count": len(category["topics"])
        })
    
    return {
        "code": 0,
        "data": topics
    }


@router.get("/topics/{category_id}")
async def get_topics_by_category(category_id: str):
    """
    Get topics by category
    """
    if category_id not in GRAMMAR_TOPICS:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category = GRAMMAR_TOPICS[category_id]
    topics = []
    
    for topic in category["topics"]:
        topics.append({
            "id": topic["id"],
            "name": topic["name"],
            "description": topic["description"],
            "example_count": len(topic["examples"]),
            "exercise_count": len(topic["exercises"])
        })
    
    return {
        "code": 0,
        "data": {
            "category": category["name"],
            "topics": topics
        }
    }


@router.post("/learn")
async def learn_grammar(request: GrammarLearnRequest):
    """
    Get grammar explanation, examples and exercises
    """
    logger.info(f"Learn grammar: topic_id={request.topic_id}")
    
    # 查找语法点
    topic = None
    for category in GRAMMAR_TOPICS.values():
        for t in category["topics"]:
            if t["id"] == request.topic_id:
                topic = t
                break
        if topic:
            break
    
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # 记录学习统计
    try:
        from db.connection import get_db
        from models import Statistics
        from datetime import datetime
        
        session = next(get_db())
        today = datetime.now().strftime("%Y-%m-%d")
        stats = session.query(Statistics).filter(Statistics.date == today).first()
        
        if stats:
            stats.grammar_learned += 1
            session.commit()
        session.close()
    except Exception as e:
        logger.warning(f"Failed to record grammar learn stats: {e}")
    
    return {
        "code": 0,
        "data": {
            "id": topic["id"],
            "name": topic["name"],
            "description": topic["description"],
            "formula": topic.get("formula", ""),
            "examples": topic["examples"],
            "exercises": topic["exercises"]
        }
    }


@router.post("/exercise")
async def submit_exercise(request: GrammarExerciseRequest):
    """
    Submit exercise answer and get feedback
    """
    logger.info(f"Submit exercise: topic={request.topic_id}, exercise={request.exercise_id}, answer={request.answer}")
    
    # 查找语法点和练习
    topic = None
    exercise = None
    
    for category in GRAMMAR_TOPICS.values():
        for t in category["topics"]:
            if t["id"] == request.topic_id:
                topic = t
                if 0 <= request.exercise_id < len(t["exercises"]):
                    exercise = t["exercises"][request.exercise_id]
                break
        if topic:
            break
    
    if not topic or not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # 检查答案
    user_answer = request.answer.lower().strip()
    correct_answer = exercise["answer"].lower().strip()
    correct = user_answer == correct_answer
    
    result = {
        "correct": correct,
        "correct_answer": exercise["answer"],
        "explanation": exercise.get("explanation", ""),
        "is_last": request.exercise_id >= len(topic["exercises"]) - 1
    }
    
    # 如果用户提供了解释，也包含
    if exercise.get("explanation"):
        result["explanation"] = exercise["explanation"]
    else:
        result["explanation"] = "答案正确！" if correct else f"正确答案是: {exercise['answer']}"
    
    # 记录练习统计
    try:
        from db.connection import get_db
        from models import Statistics
        from datetime import datetime
        
        session = next(get_db())
        today = datetime.now().strftime("%Y-%m-%d")
        stats = session.query(Statistics).filter(Statistics.date == today).first()
        
        if stats:
            stats.grammar_exercises += 1
            session.commit()
        session.close()
    except Exception as e:
        logger.warning(f"Failed to record grammar exercise stats: {e}")
    
    return {
        "code": 0,
        "data": result
    }


@router.get("/recommend")
async def recommend_grammar():
    """
    Recommend grammar topics based on user's level
    """
    # 简单推荐：返回第一个分类的第二个语法点
    recommendations = []
    
    categories = list(GRAMMAR_TOPICS.keys())
    if categories:
        first_cat = GRAMMAR_TOPICS[categories[0]]
        if first_cat["topics"]:
            # 推荐简单主题
            recommendations.append({
                "id": first_cat["topics"][0]["id"],
                "name": first_cat["topics"][0]["name"],
                "category": first_cat["name"],
                "reason": "适合初学者开始学习"
            })
            
            # 如果有更多主题，推荐进阶
            if len(first_cat["topics"]) > 1:
                recommendations.append({
                    "id": first_cat["topics"][1]["id"],
                    "name": first_cat["topics"][1]["name"],
                    "category": first_cat["name"],
                    "reason": "进阶学习"
                })
    
    return {
        "code": 0,
        "data": recommendations
    }


class GrammarGenerateRequest(BaseModel):
    category: str
    count: int = 1


def _repair_truncated_json(text: str) -> str | None:
    """智能修复被截断的JSON响应"""
    import re
    
    text = text.strip()
    if not text:
        return None
    
    # 检查是否是被截断的JSON数组
    if not text.startswith('['):
        return None
    
    # 统计括号平衡
    bracket_count = 0
    brace_count = 0
    
    for char in text:
        if char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
        elif char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
    
    # 如果数组没有正确闭合，尝试修复
    if bracket_count > 0:
        # 找到最后一个完整的对象并闭合数组
        # 策略：移除末尾不完整的部分，添加闭合括号
        
        # 尝试找到最后一个完整的练习对象
        # 从字符串末尾向前查找，直到找到平衡的 }
        end_pos = len(text)
        brace_balance = 0
        
        for i in range(len(text) - 1, -1, -1):
            char = text[i]
            if char == '}':
                brace_balance += 1
            elif char == '{':
                brace_balance -= 1
            
            if brace_balance == 0 and i < len(text) - 1:
                # 找到一个完整对象的结尾
                # 检查这个位置附近是否是完整的语法点
                end_pos = i + 1
                break
        
        # 裁剪到最后一个完整对象
        repaired = text[:end_pos]
        
        # 确保数组被正确闭合
        repaired = repaired.rstrip(',').rstrip(' ')
        if not repaired.endswith(']'):
            repaired += ']'
        
        # 验证修复后的JSON是否有效
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass
    
    # 备选策略：尝试移除可能不完整的最后一个对象
    if brace_count > 0:
        # 移除末尾不完整的部分（从 "exercises" 截断处开始）
        # 查找最后一个完整的 name 字段位置
        last_name_match = list(re.finditer(r'"name":\s*"[^"]+"', text))
        if last_name_match:
            last_name = last_name_match[-1]
            # 找到这个 name 所属对象的结束位置
            # 从该位置向后找到对应的 }
            start_search = last_name.end()
            brace_check = 0
            end_idx = start_search
            
            for i in range(start_search, len(text)):
                if text[i] == '{':
                    brace_check += 1
                elif text[i] == '}':
                    brace_check -= 1
                if brace_check == 0:
                    end_idx = i + 1
                    break
            
            repaired = text[:end_idx].rstrip(',').rstrip(' ')
            if not repaired.endswith(']'):
                repaired += ']'
            
            try:
                json.loads(repaired)
                return repaired
            except:
                pass
    
    return None


@router.post("/generate")
async def generate_grammar(request: GrammarGenerateRequest):
    """
    AI生成语法点
    """
    from services.ai_chat import chat_service
    import json
    import re

    logger.info(f"Generate grammar: category={request.category}, count={request.count}")

    prompt = f"""请生成{request.count}个关于"{request.category}"的英语语法点。

请严格按以下JSON格式返回（务必精简，每个语法点只包含核心字段）：

[
  {{"name": "语法点名称", "description": "一句话描述", "formula": "公式", "examples": ["例句1"], "exercises": [{{"type": "choice", "question": "题目", "answer": "答案", "options": ["A", "B", "C", "D"]}}]}}
]

要求：
1. 只返回JSON数组，不要任何前缀后缀
2. 每个语法点的exercises只需1道题
3. examples只需1个例句
4. description最短只写一句话
5. 必须确保JSON完整可解析"""

    try:
        result = await chat_service.chat(prompt, scene="exam")
        reply = result.get("reply", "")

        # 记录原始回复以便调试
        logger.info(f"AI response (first 500 chars): {reply[:500]}")

        # 清理回复内容，移除可能的markdown标记
        reply = reply.strip()
        reply = reply.replace('```json', '').replace('```', '').replace('```markdown', '').replace('```xml', '')

        # 解析JSON - 尝试多种方式
        topics = []
        parse_errors = []

        # 方法1: 尝试直接解析
        try:
            topics = json.loads(reply)
            logger.info("Method 1 succeeded: direct parse")
        except json.JSONDecodeError as e:
            parse_errors.append(f"Method 1 failed: {e}")

        # 方法2: 尝试正则提取JSON数组
        if not topics:
            try:
                match = re.search(r'\[.*\]', reply, re.DOTALL)
                if match:
                    topics = json.loads(match.group())
                    logger.info("Method 2 succeeded: regex extract array")
            except (json.JSONDecodeError, AttributeError) as e:
                parse_errors.append(f"Method 2 failed: {e}")

        # 方法3: 尝试正则提取JSON对象，然后组合成数组
        if not topics:
            try:
                obj_matches = re.findall(r'\{[^{}]*"name"[^{}]*\}', reply)
                if obj_matches:
                    topics = []
                    for obj_str in obj_matches:
                        try:
                            obj = json.loads(obj_str)
                            if "name" in obj:
                                topics.append(obj)
                        except:
                            pass
                    if topics:
                        logger.info(f"Method 3 succeeded: found {len(topics)} objects")
            except Exception as e:
                parse_errors.append(f"Method 3 failed: {e}")

        # 方法4: 尝试查找被包裹在各种标签中的JSON
        if not topics:
            try:
                # 尝试提取 <response> 或其他标签中的内容
                patterns = [
                    r'<response>(.*?)</response>',
                    r'<result>(.*?)</result>',
                    r'\{.*?"name".*?"description".*?\}(?:,\s*\{.*?\})*'
                ]
                for pattern in patterns:
                    match = re.search(pattern, reply, re.DOTALL)
                    if match:
                        try:
                            topics = json.loads(match.group())
                            if topics:
                                logger.info(f"Method 4 succeeded: pattern {pattern}")
                                break
                        except:
                            continue
            except Exception as e:
                parse_errors.append(f"Method 4 failed: {e}")

        # 方法5: 尝试逐行解析，查找有效的JSON对象
        if not topics:
            try:
                lines = reply.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            obj = json.loads(line)
                            if "name" in obj and "description" in obj:
                                topics.append(obj)
                        except:
                            continue
                if topics:
                    logger.info(f"Method 5 succeeded: found {len(topics)} objects from lines")
            except Exception as e:
                parse_errors.append(f"Method 5 failed: {e}")

        # 方法6: 智能修复截断的JSON（关键新增）
        if not topics:
            try:
                repaired = _repair_truncated_json(reply)
                if repaired:
                    topics = json.loads(repaired)
                    if topics:
                        logger.info(f"Method 6 succeeded: repaired truncated JSON")
            except Exception as e:
                parse_errors.append(f"Method 6 failed: {e}")

        # 如果所有方法都失败了，记录错误并提供更友好的错误信息
        if not topics:
            logger.error(f"All parsing methods failed. Errors: {'; '.join(parse_errors)}")
            logger.error(f"Original reply: {reply[:1000]}")
            raise HTTPException(
                status_code=500,
                detail=f"AI返回的数据格式无法解析，已记录日志。请尝试简化查询或稍后重试。"
            )

        # 验证返回数据的格式
        valid_topics = []
        for t in topics:
            if isinstance(t, dict) and "name" in t:
                valid_topics.append({
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "formula": t.get("formula", ""),
                    "examples": t.get("examples", []),
                    "exercises": t.get("exercises", [])
                })

        if not valid_topics:
            logger.error(f"No valid topics found after validation. Topics: {topics}")
            raise HTTPException(status_code=500, detail="AI返回的语法点数据格式不完整，请重试")

        logger.info(f"Generated {len(valid_topics)} grammar topics")

        return {
            "code": 0,
            "data": {
                "topics": valid_topics
            }
        }
    except HTTPException:
        # 重新抛出HTTPException，不做额外处理
        raise
    except Exception as e:
        logger.error(f"Generate grammar error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成语法失败: {str(e)}")