from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Database URL for async operations
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
)

# Create session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Base class for models
Base = declarative_base()

# Metadata
metadata = MetaData()

async def init_db():
    """Initialize database tables"""
    try:
        async with async_engine.begin() as conn:
            # Import models here to ensure they're registered
            from app.models.sqlalchemy_models import (
                Problem, UserProgress, Attempt, Hint, 
                HintDelivery, HintEvaluation
            )
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

async def close_db():
    """Close database connections"""
    try:
        await async_engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")

# Dependency to get database session
async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """Get synchronous database session for migrations"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 