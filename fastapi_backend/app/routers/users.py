from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import pydantic_models as p
from app.models import sqlalchemy_models as m

router = APIRouter()

@router.get("/{user_id}/progress", response_model=p.UserProgress)
async def get_user_progress(user_id: int, problem_id: int, db: AsyncSession = Depends(get_db)):
    """Get user progress for a specific problem"""
    result = await db.execute(
        select(m.UserProgress).filter_by(user_id=user_id, problem_id=problem_id)
    )
    progress = result.scalar_one_or_none()
    
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User progress not found")
        
    return progress 