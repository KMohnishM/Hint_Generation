from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class HintType(str, Enum):
    CONCEPTUAL = "conceptual"
    APPROACH = "approach"
    IMPLEMENTATION = "implementation"
    DEBUG = "debug"

class AttemptStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

# Base Models
class ProblemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

class ProblemCreate(ProblemBase):
    pass

class Problem(ProblemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserProgressBase(BaseModel):
    user_id: int = Field(..., gt=0)
    problem_id: int = Field(..., gt=0)
    attempts_count: int = Field(default=0, ge=0)
    failed_attempts_count: int = Field(default=0, ge=0)
    current_hint_level: int = Field(default=1, ge=1, le=5)

class UserProgressCreate(UserProgressBase):
    pass

class UserProgress(UserProgressBase):
    id: int
    last_activity: datetime
    is_stuck: bool
    
    class Config:
        from_attributes = True

class AttemptBase(BaseModel):
    user_id: int = Field(..., gt=0)
    problem_id: int = Field(..., gt=0)
    code: str = Field(..., min_length=1)
    status: AttemptStatus = AttemptStatus.PENDING

class AttemptCreate(AttemptBase):
    pass

class Attempt(AttemptBase):
    id: int
    evaluation_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class HintBase(BaseModel):
    problem_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1)
    level: int = Field(..., ge=1, le=5)
    hint_type: HintType = HintType.CONCEPTUAL

class HintCreate(HintBase):
    pass

class Hint(HintBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class HintDeliveryBase(BaseModel):
    hint_id: int = Field(..., gt=0)
    user_id: int = Field(..., gt=0)
    attempt_id: int = Field(..., gt=0)
    is_auto_triggered: bool = False

class HintDeliveryCreate(HintDeliveryBase):
    pass

class HintDelivery(HintDeliveryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class HintEvaluationBase(BaseModel):
    hint_id: int = Field(..., gt=0)
    safety_score: float = Field(..., ge=0.0, le=1.0)
    helpfulness_score: float = Field(..., ge=0.0, le=1.0)
    quality_score: float = Field(..., ge=0.0, le=1.0)
    progress_alignment_score: float = Field(..., ge=0.0, le=1.0)
    pedagogical_value_score: float = Field(..., ge=0.0, le=1.0)

class HintEvaluationCreate(HintEvaluationBase):
    pass

class HintEvaluation(HintEvaluationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Request/Response Models
class HintRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    problem_id: int = Field(..., gt=0)
    user_code: str = Field(..., min_length=1)
    problem_data: Optional[Dict[str, Any]] = None

class HintResponse(BaseModel):
    hint_content: str
    hint_level: int
    hint_type: HintType
    attempt_evaluation: Dict[str, Any]
    hint_evaluation: Dict[str, float]
    user_progress: UserProgress

class AutoTriggerRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    problem_id: int = Field(..., gt=0)
    user_code: str = Field(..., min_length=1)
    last_attempt_status: Optional[AttemptStatus] = None
    last_attempt_error: Optional[str] = None
    test_cases_passed: Optional[int] = None
    total_test_cases: Optional[int] = None

class AutoTriggerResponse(BaseModel):
    should_trigger: bool
    reason: str
    hint_type: HintType
    hint_level: int

class FeedbackRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    hint_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None

class FeedbackResponse(BaseModel):
    message: str
    hint_id: int
    rating: int

# API Response Models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None 