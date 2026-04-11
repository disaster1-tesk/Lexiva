"""
FastAPI Main Application
AI English Learning System - Experience Priority Version
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI English Learning System",
    description="An AI-powered English learning platform for students",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api import chat, vocabulary, writing, pronunciation, listening, statistics, settings

app.include_router(chat.router)
app.include_router(vocabulary.router)
app.include_router(writing.router)
app.include_router(pronunciation.router)
app.include_router(listening.router)
app.include_router(statistics.router)
app.include_router(settings.router)

# Include WebSocket
from websocket.manager import router as ws_router
app.include_router(ws_router)


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