"""
WebSocket Manager for real-time communication
Supports both chat and full-duplex phone call modes
"""
import asyncio
import json
import base64
import os
from datetime import datetime
from typing import Dict, Set, Optional
from socketio import AsyncManager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ai_chat import AIChatService
from services.ai_whisper import whisper_service
from services.ai_tts import tts_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 尝试导入 OpenAI SDK 用于流式生成 (可选)
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.chat_service = AIChatService()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total: {len(self.active_connections)}")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


class PhoneCallManager:
    """Full-duplex phone call manager with interrupt detection and streaming support"""
    
    def __init__(self):
        self.active_calls: Dict[str, dict] = {}
        self.chat_service = AIChatService()
        # 配置参数
        self.INTERRUPT_THRESHOLD = 0.3  # 音量阈值，判断是否在说话
        self.SILENCE_TIMEOUT = 2.0  # 静默超时时间（秒），超过则认为用户说完
        self.AUDIO_CHUNK_MS = 300  # 音频分片大小
        # 流式配置
        self.STREAM_TTS = os.getenv("STREAM_TTS", "true").lower() == "true"
        self.STREAM_LLM = os.getenv("STREAM_LLM", "false").lower() == "true"
    
    async def start_call(self, websocket: WebSocket, client_id: str, scene: str = "daily"):
        """Start a new phone call session"""
        # WebSocket 已在外层 accept，这里不再重复
        
        self.active_calls[client_id] = {
            "websocket": websocket,
            "scene": scene,
            "is_speaking": False,
            "ai_is_speaking": False,
            "last_audio_time": 0,
            "conversation_history": [],
            "intro_sent": False,
            "streaming_task": None  # 用于取消流式生成
        }

        logger.info(f"Phone call started: client_id={client_id}, scene={scene}")
        
        # 通知前端通话已建立，显示"等待用户说话"状态
        await self.send_to_client(client_id, {
            "type": "call_status",
            "status": "waiting",
            "message": "请点击麦克风开始说话"
        })
    
    async def _send_intro(self, client_id: str, scene: str):
        """Send AI introduction based on scene"""
        intro_prompts = {
            "daily": "Hello! I'm your English conversation partner. Let's talk about something interesting today. How have you been?",
            "travel": "Hi there! Imagine we're planning a trip together. Where would you like to go and what would you like to do?",
            "business": "Hello! Let's practice some business communication. I'm your colleague in a meeting. What would you like to discuss?",
            "academic": "Hi! Let's have an academic discussion. What topic would you like to explore today?",
            "roleplay": "Hello! I'm ready for our roleplay scenario. Please describe the situation, and we'll begin!"
        }
        
        intro = intro_prompts.get(scene, intro_prompts["daily"])
        
        # 根据配置选择发送方式
        if self.STREAM_TTS and hasattr(tts_service, '_get_provider'):
            # 尝试使用流式 TTS
            await self._send_intro_stream(client_id, intro)
        else:
            # 使用普通 TTS
            audio_response = await tts_service.synthesize(intro)
            
            await self.send_to_client(client_id, {
                "type": "ai_response",
                "text": intro,
                "audio": audio_response.get("audio", "") if audio_response.get("success") else "",
                "status": "speaking"
            })
            
            # 更新状态
            if client_id in self.active_calls:
                self.active_calls[client_id]["ai_is_speaking"] = True
                self.active_calls[client_id]["intro_sent"] = True
    
    async def _send_intro_stream(self, client_id: str, text: str):
        """Send AI response using streaming TTS"""
        try:
            # 获取 TTS provider 检查是否支持流式
            provider = tts_service._get_provider()
            has_stream = hasattr(provider, 'synthesize_stream')
            
            if not has_stream:
                # 不支持流式，降级到普通方式
                audio_response = await tts_service.synthesize(text)
                await self.send_to_client(client_id, {
                    "type": "ai_response",
                    "text": text,
                    "audio": audio_response.get("audio", "") if audio_response.get("success") else "",
                    "status": "speaking"
                })
                return
            
            # 使用流式 TTS
            stream_result = await provider.synthesize_stream(text, "female")
            
            if stream_result.get("success"):
                for i, chunk in enumerate(stream_result.get("chunks", [])):
                    # 检查是否被中断
                    if client_id not in self.active_calls:
                        break
                    
                    if self.active_calls[client_id].get("ai_is_speaking") == False:
                        # 用户打断了，停止发送
                        break
                    
                    # 发送音频块
                    await self.send_to_client(client_id, {
                        "type": "audio_chunk",
                        "audio": chunk.get("audio", ""),
                        "is_final": chunk.get("is_final", False),
                        "text": text  # 可选：发送已生成的文本片段
                    })
                    
                    # 短暂延迟避免发送过快
                    if i > 0 and i % 5 == 0:
                        await asyncio.sleep(0.01)
            else:
                # 流式失败，降级
                audio_response = await tts_service.synthesize(text)
                await self.send_to_client(client_id, {
                    "type": "ai_response",
                    "text": text,
                    "audio": audio_response.get("audio", "") if audio_response.get("success") else "",
                    "status": "speaking"
                })
        except Exception as e:
            logger.error(f"Stream TTS error: {e}")
            # 降级到普通方式
            audio_response = await tts_service.synthesize(text)
            await self.send_to_client(client_id, {
                "type": "ai_response",
                "text": text,
                "audio": audio_response.get("audio", "") if audio_response.get("success") else "",
                "status": "speaking"
            })
        
        # 更新状态
        if client_id in self.active_calls:
            self.active_calls[client_id]["ai_is_speaking"] = True
            self.active_calls[client_id]["intro_sent"] = True
        
        intro = intro_prompts.get(scene, intro_prompts["daily"])
        
        # 生成语音
        audio_response = await tts_service.synthesize(intro)
        
        await self.send_to_client(client_id, {
            "type": "ai_response",
            "text": intro,
            "audio": audio_response.get("audio", "") if audio_response.get("success") else "",
            "status": "speaking"
        })
        
        # 更新状态
        if client_id in self.active_calls:
            self.active_calls[client_id]["ai_is_speaking"] = True
            self.active_calls[client_id]["intro_sent"] = True
    
    async def handle_audio(self, client_id: str, audio_data: str, is_final: bool = False, mime_type: str = "audio/wav"):
        """Handle incoming audio from user (with interrupt detection)"""
        if client_id not in self.active_calls:
            return
        
        call_state = self.active_calls[client_id]
        
        # 如果 AI 正在说话，用户开始说话则打断 AI
        if call_state["ai_is_speaking"] and is_final:
            await self._interrupt_ai(client_id)
        
        if not audio_data or len(audio_data) < 100:
            return
        
        try:
            # 语音识别 - 传递 mime_type 以便正确处理音频格式
            result = await whisper_service.transcribe_base64(audio_data, language="en", mime_type=mime_type)
            
            if not result.get("success"):
                return
            
            recognized_text = result.get("text", "").strip()
            if not recognized_text:
                return
            
            # 发送识别结果给用户
            await self.send_to_client(client_id, {
                "type": "recognition",
                "text": recognized_text,
                "interim": not is_final
            })
            
            # 完整句子，处理对话
            if is_final:
                await self._process_user_message(client_id, recognized_text)
                
        except Exception as e:
            logger.error(f"Audio handling error: {e}")
    
    async def _interrupt_ai(self, client_id: str):
        """Interrupt AI when user starts speaking"""
        if client_id not in self.active_calls:
            return
        
        call_state = self.active_calls[client_id]
        call_state["ai_is_speaking"] = False
        
        # 取消正在进行的流式任务
        if call_state.get("streaming_task") and not call_state["streaming_task"].done():
            call_state["streaming_task"].cancel()
            call_state["streaming_task"] = None
        
        # 通知前端停止播放
        await self.send_to_client(client_id, {
            "type": "call_status",
            "status": "interrupted",
            "message": "我听到你了，请继续..."
        })
        
        logger.info(f"AI interrupted by user: {client_id}")
    
    async def _process_user_message(self, client_id: str, user_message: str):
        """Process user's recognized message and generate AI response"""
        if client_id not in self.active_calls:
            return
        
        call_state = self.active_calls[client_id]
        
        # 通知正在思考
        await self.send_to_client(client_id, {
            "type": "call_status",
            "status": "thinking",
            "message": "让我想想..."
        })
        
        # 获取 AI 回复
        response = await self.chat_service.chat(user_message, call_state["scene"])
        
        reply_text = response.get("reply", "I understand. Can you tell me more?")
        
        # 生成语音
        audio_response = await tts_service.synthesize(reply_text)
        
        # 发送 AI 回复
        await self.send_to_client(client_id, {
            "type": "ai_response",
            "text": reply_text,
            "audio": audio_response.get("audio", "") if audio_response.get("success") else "",
            "status": "speaking"
        })
        
        # 更新状态
        call_state["ai_is_speaking"] = True
        
        # 保存对话历史
        call_state["conversation_history"].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply_text}
        ])
        
        # 限制历史长度
        if len(call_state["conversation_history"]) > 10:
            call_state["conversation_history"] = call_state["conversation_history"][-10:]
    
    async def end_call(self, client_id: str):
        """End phone call"""
        if client_id in self.active_calls:
            call_state = self.active_calls[client_id]
            
            # 发送结束语
            await self.send_to_client(client_id, {
                "type": "ai_response",
                "text": "Thank you for practicing with me today! Keep up the good work!",
                "audio": "",
                "status": "ended"
            })
            
            # 清理
            del self.active_calls[client_id]
            logger.info(f"Phone call ended: {client_id}")
    
    async def handle_text(self, client_id: str, message: str):
        """Handle text message during call"""
        if client_id not in self.active_calls:
            return
        
        call_state = self.active_calls[client_id]
        
        # 切换场景
        if message.startswith("/scene "):
            new_scene = message.split(" ", 1)[1]
            call_state["scene"] = new_scene
            await self.send_to_client(client_id, {
                "type": "call_status",
                "status": "scene_changed",
                "message": f"场景已切换为: {new_scene}"
            })
            return
        
        # 处理普通文本
        await self._process_user_message(client_id, message)
    
    async def send_to_client(self, client_id: str, message: dict):
        """Send message to client"""
        if client_id in self.active_calls:
            websocket = self.active_calls[client_id]["websocket"]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Send error: {e}")
    
    def disconnect(self, client_id: str):
        """Handle client disconnect"""
        if client_id in self.active_calls:
            del self.active_calls[client_id]
            logger.info(f"Phone call disconnected: {client_id}")


manager = ConnectionManager()
phone_manager = PhoneCallManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time voice chat"""
    logger.info("New WebSocket connection request")
    
    client_id = None
    try:
        # Wait for client identification
        first_message = await websocket.receive_text()
        data = json.loads(first_message)
        
        if data.get("type") == "init":
            client_id = data.get("client_id", "anonymous")
            logger.info(f"WebSocket init: client_id={client_id}")
            
            await manager.connect(websocket, client_id)
            
            # Send acknowledgment
            await manager.send_message(client_id, {
                "type": "connected",
                "message": "Connected to AI English Tutor"
            })
            
            logger.info(f"WebSocket connected: client_id={client_id}")
            
            # Handle messages loop
            while True:
                try:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    logger.info(f"WebSocket message: client_id={client_id}, type={msg_type}")
                    
                    if msg_type == "text":
                        # Process text message
                        user_input = data.get("content", "")
                        scene = data.get("scene", "daily")
                        
                        # Get AI response
                        response = await manager.chat_service.chat(user_input, scene)
                        
                        await manager.send_message(client_id, {
                            "type": "text",
                            "reply": response["reply"],
                            "corrections": response.get("corrections", [])
                        })
                        
                        logger.info(f"WebSocket response sent: client_id={client_id}, reply_len={len(response.get('reply', ''))}")
                    
                    elif msg_type == "audio":
                        # 实时语音输入 - 流式处理
                        audio_data = data.get("data", "")
                        is_final = data.get("is_final", False)
                        mime_type = data.get("mime_type", "audio/wav")
                        
                        if audio_data:
                            # 调用 Whisper 进行语音识别
                            result = await whisper_service.transcribe_base64(audio_data, language="en", mime_type=mime_type)
                            
                            if result.get("success") and result.get("text"):
                                recognized_text = result.get("text", "")
                                
                                if is_final:
                                    # 完整句子，发送到 AI 对话
                                    response = await manager.chat_service.chat(recognized_text, scene)
                                    
                                    # AI 响应转语音
                                    audio_response = await tts_service.synthesize(response.get("reply", ""))
                                    
                                    await manager.send_message(client_id, {
                                        "type": "text",
                                        "reply": response.get("reply", ""),
                                        "corrections": response.get("corrections", []),
                                        "recognized_text": recognized_text,
                                        "audio": audio_response.get("audio", "") if audio_response.get("success") else "",
                                        "is_final": True
                                    })
                                else:
                                    # 实时识别中间结果
                                    await manager.send_message(client_id, {
                                        "type": "interim",
                                        "recognized_text": recognized_text,
                                        "is_final": False
                                    })
                            elif not result.get("success"):
                                # 识别失败
                                await manager.send_message(client_id, {
                                    "type": "error",
                                    "message": result.get("error", "语音识别失败")
                                })
                    
                    elif msg_type == "ping":
                        await manager.send_message(client_id, {"type": "pong"})
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client: {client_id}")
                    continue
                    
        else:
            # No client ID, reject connection
            logger.warning(f"WebSocket invalid init: no client_id")
            await websocket.close(code=4004)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: client_id={client_id}")
        if client_id:
            manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if client_id:
            manager.disconnect(client_id)


@router.websocket("/ws/phone")
async def websocket_phone_call(websocket: WebSocket):
    """WebSocket endpoint for full-duplex phone call"""
    logger.info("New phone call connection request")
    
    client_id = None
    try:
        # Accept the WebSocket connection first
        await websocket.accept()
        
        # Wait for client identification
        first_message = await websocket.receive_text()
        data = json.loads(first_message)
        
        if data.get("type") == "start_call":
            client_id = data.get("client_id", f"phone_{get_timestamp()}")
            scene = data.get("scene", "daily")
            logger.info(f"Phone call start: client_id={client_id}, scene={scene}")
            
            # Start the phone call
            await phone_manager.start_call(websocket, client_id, scene)
            
            # Handle messages loop
            while True:
                try:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    
                    if msg_type == "audio":
                        # 处理用户音频输入（实时流式）
                        audio_data = data.get("data", "")
                        is_final = data.get("is_final", False)
                        mime_type = data.get("mime_type", "audio/wav")  # 获取音频格式
                        await phone_manager.handle_audio(client_id, audio_data, is_final, mime_type)
                    
                    elif msg_type == "text":
                        # 处理文本消息
                        text = data.get("content", "")
                        await phone_manager.handle_text(client_id, text)
                    
                    elif msg_type == "end_call":
                        # 结束通话
                        await phone_manager.end_call(client_id)
                        break
                    
                    elif msg_type == "interrupt":
                        # 用户打断 AI 说话
                        await phone_manager._interrupt_ai(client_id)
                    
                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong"})
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from phone client: {client_id}")
                    continue
                    
        else:
            logger.warning(f"Phone call invalid init: no start_call type")
            await websocket.close(code=4004)
            
    except WebSocketDisconnect:
        logger.info(f"Phone call disconnected: client_id={client_id}")
        if client_id:
            phone_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Phone call WebSocket error: {e}", exc_info=True)
        if client_id:
            phone_manager.disconnect(client_id)


def get_timestamp():
    return int(datetime.now().timestamp() * 1000)