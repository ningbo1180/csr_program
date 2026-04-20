"""
CSR GenAI Backend Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db
from app.api import projects, documents, chapters, logs, ai, export

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("CSR GenAI Backend starting up...")
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("CSR GenAI Backend shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="CSR GenAI API",
    description="API for Clinical Study Report Generation Platform",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(chapters.router)
app.include_router(logs.router)
app.include_router(ai.router)
app.include_router(export.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "CSR GenAI Backend is running"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CSR GenAI API",
        "version": "0.1.0",
        "status": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload_mode = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload_mode
    )
