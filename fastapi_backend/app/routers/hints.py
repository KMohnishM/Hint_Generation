from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.models import pydantic_models as p
from app.models import sqlalchemy_models as m
from app.services.hint_chain import HintChain

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize the hint chain service (could be a dependency)
hint_chain = HintChain()

async def _get_or_create_problem(db: AsyncSession, problem_id: int, problem_data: dict = None) -> m.Problem:
    """Get existing problem or create new one if needed"""
    logger.info(f"🔍 Looking up problem with ID: {problem_id}")
    problem = await db.get(m.Problem, problem_id)
    if problem:
        logger.info(f"✅ Found existing problem: {problem.title}")
        return problem
    
    logger.info(f"❌ Problem {problem_id} not found")
    if problem_data:
        logger.info("📝 Creating new problem from provided data")
        problem = m.Problem(
            id=problem_id,
            title=problem_data.get('title', 'Untitled Problem'),
            description=problem_data.get('description', ''),
            difficulty=problem_data.get('difficulty', 'medium')
        )
        db.add(problem)
        await db.commit()
        await db.refresh(problem)
        logger.info(f"✅ Created new problem: {problem.title} (ID: {problem.id})")
        return problem
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Problem not found and no problem data provided"
    )

async def _get_or_create_user_progress(db: AsyncSession, user_id: int, problem: m.Problem) -> m.UserProgress:
    """Get or create user progress"""
    logger.info(f"👤 Getting user progress for user {user_id} on problem {problem.id}")
    
    result = await db.execute(
        select(m.UserProgress).filter_by(user_id=user_id, problem_id=problem.id)
    )
    progress = result.scalar_one_or_none()
    
    if progress:
        logger.info(f"✅ Found existing progress: {progress.attempts_count} attempts")
        return progress
        
    logger.info("📝 Creating new user progress record")
    progress = m.UserProgress(
        user_id=user_id,
        problem_id=problem.id
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    logger.info(f"✅ Created new progress record for user {user_id}")
    return progress

async def _get_previous_hints(db: AsyncSession, user_id: int, problem_id: int, limit: int = 5):
    """Get previous hints for this user and problem"""
    logger.info(f"📚 Getting previous hints for user {user_id} on problem {problem_id}")
    result = await db.execute(
        select(m.HintDelivery)
        .filter_by(user_id=user_id)
        .join(m.Hint)
        .filter(m.Hint.problem_id == problem_id)
        .order_by(m.HintDelivery.created_at.desc())
        .limit(limit)
        .options(selectinload(m.HintDelivery.hint))
    )
    hints = result.scalars().all()
    logger.info(f"✅ Found {len(hints)} previous hints")
    return [h.hint.content for h in hints]

async def _create_attempt(db: AsyncSession, user_id: int, problem: m.Problem, user_code: str) -> m.Attempt:
    """Create an attempt record for the user"""
    logger.info(f"📝 Creating attempt record for user {user_id} on problem {problem.id}")
    
    attempt_evaluation = await hint_chain.evaluate_attempt_only(
        problem_description=problem.description,
        user_code=user_code
    )
    
    attempt = m.Attempt(
        user_id=user_id,
        problem_id=problem.id,
        code=user_code,
        status='failed' if not attempt_evaluation['success'] else 'success',
        evaluation_details=attempt_evaluation
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    
    logger.info(f"✅ Created attempt record (ID: {attempt.id}, Status: {attempt.status})")
    return attempt

@router.post("/request_hint", response_model=p.HintResponse)
async def request_hint(request: p.HintRequest, db: AsyncSession = Depends(get_db)):
    """Request a hint for a problem"""
    logger.info(f"🎯 Received hint request for user {request.user_id}, problem {request.problem_id}")

    problem = await _get_or_create_problem(db, request.problem_id, request.problem_data)
    progress = await _get_or_create_user_progress(db, request.user_id, problem)
    
    # Create an attempt record
    attempt = await _create_attempt(db, request.user_id, problem, request.user_code)

    # Update progress
    progress.attempts_count += 1
    if attempt.status == 'failed':
        progress.failed_attempts_count += 1
    
    # Fix timezone issue: ensure both datetimes are timezone-aware
    current_time = datetime.now(timezone.utc)
    last_activity = progress.last_activity.replace(tzinfo=timezone.utc) if progress.last_activity.tzinfo is None else progress.last_activity
    time_since_last_attempt = (current_time - last_activity).total_seconds()
    progress.last_activity = current_time
    
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    
    previous_hints_text = await _get_previous_hints(db, request.user_id, problem.id)

    # Prepare input for the chain
    chain_input = {
        "problem_description": problem.description,
        "user_code": request.user_code,
        "attempts_count": progress.attempts_count,
        "failed_attempts_count": progress.failed_attempts_count,
        "current_hint_level": progress.current_hint_level,
        "time_since_last_attempt": time_since_last_attempt,
        "previous_hints": previous_hints_text,
        "hint_level": progress.current_hint_level,
        "hint_type": "conceptual" # This gets updated inside the chain
    }
    
    logger.info("🔄 Running HintChain workflow...")
    result = await hint_chain.process_hint_request(chain_input)
    
    # Update user progress with new hint level from the chain
    new_hint_level = result.get('updated_hint_level', progress.current_hint_level)
    if new_hint_level != progress.current_hint_level:
        logger.info(f"📈 Updating hint level: {progress.current_hint_level} → {new_hint_level}")
        progress.current_hint_level = new_hint_level
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    # Create and store the hint and its delivery record
    hint = m.Hint(
        problem_id=problem.id,
        content=result['generated_hint'],
        level=new_hint_level,
        hint_type=result['updated_hint_type']
    )
    db.add(hint)
    await db.commit()
    await db.refresh(hint)

    hint_delivery = m.HintDelivery(
        hint_id=hint.id,
        user_id=request.user_id,
        attempt_id=attempt.id,
        is_auto_triggered=False
    )
    db.add(hint_delivery)
    
    # Create hint evaluation record
    hint_eval = m.HintEvaluation(
        hint_id=hint.id,
        **result['hint_evaluation']
    )
    db.add(hint_eval)
    
    await db.commit()
    
    return p.HintResponse(
        hint_content=result['generated_hint'],
        hint_level=new_hint_level,
        hint_type=result['updated_hint_type'],
        attempt_evaluation=result['attempt_evaluation'],
        hint_evaluation=result['hint_evaluation'],
        user_progress=p.UserProgress.from_orm(progress)
    )

@router.post("/check_auto_trigger", response_model=p.AutoTriggerResponse)
async def check_auto_trigger(request: p.AutoTriggerRequest, db: AsyncSession = Depends(get_db)):
    """Check if a hint should be auto-triggered"""
    logger.info(f"🤖 Checking auto-trigger for user {request.user_id}, problem {request.problem_id}")
    
    problem = await db.get(m.Problem, request.problem_id)
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    progress = await _get_or_create_user_progress(db, request.user_id, problem)
    
    time_since_last_attempt = (datetime.now(timezone.utc) - progress.last_activity).total_seconds()
    
    chain_input = {
        "problem_description": problem.description,
        "user_code": request.user_code,
        "attempts_count": progress.attempts_count,
        "failed_attempts_count": progress.failed_attempts_count,
        "current_hint_level": progress.current_hint_level,
        "time_since_last_attempt": time_since_last_attempt,
        "last_attempt_status": request.last_attempt_status,
        "last_attempt_error": request.last_attempt_error,
        "test_cases_passed": request.test_cases_passed,
        "total_test_cases": request.total_test_cases
    }

    result = await hint_chain.check_auto_trigger(chain_input)
    return p.AutoTriggerResponse(**result) 