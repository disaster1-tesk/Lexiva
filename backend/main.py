"""
FastAPI Main Application
AI English Learning System - Experience Priority Version
"""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create loggers for different modules and ensure they output to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

api_logger = logging.getLogger("api")
api_logger.addHandler(console_handler)
api_logger.setLevel(logging.INFO)

services_logger = logging.getLogger("services")
services_logger.addHandler(console_handler)
services_logger.setLevel(logging.INFO)

db_logger = logging.getLogger("db")
db_logger.addHandler(console_handler)
db_logger.setLevel(logging.INFO)

websocket_logger = logging.getLogger("websocket")
websocket_logger.addHandler(console_handler)
websocket_logger.setLevel(logging.INFO)

# Create FastAPI app
app = FastAPI(
    title="AI English Learning System",
    description="An AI-powered English learning platform for students",
    version="1.0.0"
)

# Configure CORS - 从环境变量读取允许的来源，未设置时使用开发环境默认值
def get_cors_origins():
    """获取允许的 CORS 来源列表"""
    # 从环境变量读取，多个域名用逗号分隔
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    # 默认开发环境允许的来源
    return [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Create React App
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*.ngrok-free.app"
    ]

cors_origins = get_cors_origins()
logger.info(f"CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api import chat, vocabulary, writing, pronunciation, listening, statistics, settings, dictation, grammar

app.include_router(chat.router)
app.include_router(vocabulary.router)
app.include_router(writing.router)
app.include_router(pronunciation.router)
app.include_router(listening.router)
app.include_router(statistics.router)
app.include_router(settings.router)
app.include_router(dictation.router)
app.include_router(grammar.router)

# Include WebSocket
from websocket.manager import router as ws_router
app.include_router(ws_router)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    # Log request
    api_logger.info(f"→ {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    api_logger.info(f"← {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI English Learning System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Create data directory
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    logger.info(f"Created data directory: {DATA_DIR}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)