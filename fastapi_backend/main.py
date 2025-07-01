from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.database import init_db, close_db
from app.routers import hints, problems, users
from app.core.config import settings
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting FastAPI Hint Generation System...")
    await init_db()
    logger.info("✅ Database initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down FastAPI Hint Generation System...")
    await close_db()
    logger.info("✅ Database connection closed")

# Create FastAPI app
app = FastAPI(
    title="Hint Generation System",
    description="AI-powered adaptive hint generation for programming problems",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include routers
app.include_router(hints.router, prefix="/api/hints", tags=["hints"])
app.include_router(problems.router, prefix="/api/problems", tags=["problems"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hint Generation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "hint-generation-system"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 