from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models import pydantic_models as p
from app.models import sqlalchemy_models as m

router = APIRouter()

@router.post("/", response_model=p.Problem, status_code=status.HTTP_201_CREATED)
async def create_problem(problem: p.ProblemCreate, db: AsyncSession = Depends(get_db)):
    """Create a new problem"""
    new_problem = m.Problem(**problem.dict())
    db.add(new_problem)
    await db.commit()
    await db.refresh(new_problem)
    return new_problem

@router.get("/{problem_id}", response_model=p.Problem)
async def get_problem(problem_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single problem by ID"""
    problem = await db.get(m.Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    return problem

@router.get("/", response_model=List[p.Problem])
async def get_all_problems(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Get a list of all problems"""
    result = await db.execute(select(m.Problem).offset(skip).limit(limit))
    problems = result.scalars().all()
    return problems 