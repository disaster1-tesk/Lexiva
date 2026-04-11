"""
WebSocket Manager for real-time communication
"""
import asyncio
import json
from typing import Dict, Set
from socketio import AsyncManager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ai_chat import AIChatService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


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


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time voice chat"""
    client_id = None
    try:
        # Wait for client identification
        first_message = await websocket.receive_text()
        data = json.loads(first_message)
        
        if data.get("type") == "init":
            client_id = data.get("client_id", "anonymous")
            await manager.connect(websocket, client_id)
            
            # Send acknowledgment
            await manager.send_message(client_id, {
                "type": "connected",
                "message": "Connected to AI English Tutor"
            })
            
            # Handle messages loop
            while True:
                try:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    
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
                    
                    elif msg_type == "audio":
                        # Process audio message
                        audio_data = data.get("data", "")
                        # Here you would integrate Whisper for speech recognition
                        # For now, respond that audio processing is not ready
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "Audio recognition is being configured"
                        })
                    
                    elif msg_type == "ping":
                        await manager.send_message(client_id, {"type": "pong"})
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    continue
                    
        else:
            # No client ID, reject connection
            await websocket.close(code=4004)
            
    except WebSocketDisconnect:
        if client_id:
            manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if client_id:
            manager.disconnect(client_id)