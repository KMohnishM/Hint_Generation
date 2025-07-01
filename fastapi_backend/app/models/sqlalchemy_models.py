from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone
from app.database import Base

class Problem(Base):
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(10), default="medium")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user_progress = relationship("UserProgress", back_populates="problem")
    attempts = relationship("Attempt", back_populates="problem")
    hints = relationship("Hint", back_populates="problem")

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    attempts_count = Column(Integer, default=0)
    failed_attempts_count = Column(Integer, default=0)
    current_hint_level = Column(Integer, default=1)
    
    # Relationships
    problem = relationship("Problem", back_populates="user_progress")
    
    @property
    def is_stuck(self):
        """Check if user is stuck based on inactivity and failed attempts"""
        time_threshold = timedelta(minutes=5)
        current_time = datetime.now(timezone.utc)
        last_activity = self.last_activity.replace(tzinfo=timezone.utc) if self.last_activity.tzinfo is None else self.last_activity
        return (
            current_time - last_activity > time_threshold and
            self.failed_attempts_count >= 3
        )

class Attempt(Base):
    __tablename__ = "attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    code = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    evaluation_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    problem = relationship("Problem", back_populates="attempts")
    hint_deliveries = relationship("HintDelivery", back_populates="attempt")

class Hint(Base):
    __tablename__ = "hints"
    
    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    content = Column(Text, nullable=False)
    level = Column(Integer, default=1)
    hint_type = Column(String(20), default="conceptual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    problem = relationship("Problem", back_populates="hints")
    deliveries = relationship("HintDelivery", back_populates="hint")
    evaluations = relationship("HintEvaluation", back_populates="hint")

class HintDelivery(Base):
    __tablename__ = "hint_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    hint_id = Column(Integer, ForeignKey("hints.id"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"), nullable=False)
    is_auto_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    hint = relationship("Hint", back_populates="deliveries")
    attempt = relationship("Attempt", back_populates="hint_deliveries")

class HintEvaluation(Base):
    __tablename__ = "hint_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    hint_id = Column(Integer, ForeignKey("hints.id"), nullable=False)
    safety_score = Column(Float, default=0.0)
    helpfulness_score = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    progress_alignment_score = Column(Float, default=0.0)
    pedagogical_value_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    hint = relationship("Hint", back_populates="evaluations") 