"""
Advanced Personalization System for Hint Generation
- Learning style detection
- Performance pattern analysis
- Adaptive difficulty adjustment
- Cognitive load optimization
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READ_WRITE = "read_write"

class DifficultyLevel(Enum):
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5

@dataclass
class UserProfile:
    user_id: int
    learning_style: LearningStyle
    preferred_hint_length: int  # characters
    cognitive_load_preference: float  # 0-1, where 1 is high detail
    problem_solving_speed: float  # average time per attempt
    success_rate: float  # 0-1
    preferred_examples: bool
    preferred_visual_aids: bool
    preferred_step_by_step: bool

class AdvancedPersonalization:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_learning_style(self, user_attempts: List[Dict]) -> LearningStyle:
        """Analyze user's learning style based on their interaction patterns"""
        self.logger.info("🧠 Analyzing learning style...")
        
        # Count different types of interactions
        visual_interactions = 0  # Diagrams, charts, visual hints
        auditory_interactions = 0  # Verbal explanations, step-by-step
        kinesthetic_interactions = 0  # Hands-on, interactive hints
        read_write_interactions = 0  # Text-based, written explanations
        
        for attempt in user_attempts:
            hint_content = attempt.get('hint_content', '').lower()
            
            # Analyze hint content for learning style indicators
            if any(word in hint_content for word in ['diagram', 'visual', 'picture', 'chart', 'graph']):
                visual_interactions += 1
            if any(word in hint_content for word in ['step', 'process', 'sequence', 'first', 'then']):
                auditory_interactions += 1
            if any(word in hint_content for word in ['try', 'experiment', 'test', 'practice']):
                kinesthetic_interactions += 1
            if any(word in hint_content for word in ['explain', 'describe', 'define', 'concept']):
                read_write_interactions += 1
        
        # Determine dominant learning style
        interactions = {
            LearningStyle.VISUAL: visual_interactions,
            LearningStyle.AUDITORY: auditory_interactions,
            LearningStyle.KINESTHETIC: kinesthetic_interactions,
            LearningStyle.READ_WRITE: read_write_interactions
        }
        
        dominant_style = max(interactions, key=interactions.get)
        self.logger.info(f"✅ Detected learning style: {dominant_style.value}")
        return dominant_style
    
    def calculate_cognitive_load_preference(self, user_attempts: List[Dict]) -> float:
        """Calculate user's preferred cognitive load based on hint complexity preferences"""
        self.logger.info("🧮 Calculating cognitive load preference...")
        
        total_hints = len(user_attempts)
        if total_hints == 0:
            return 0.5  # Default to medium
        
        # Analyze hint complexity and user success
        complexity_scores = []
        for attempt in user_attempts:
            hint_content = attempt.get('hint_content', '')
            hint_level = attempt.get('hint_level', 1)
            was_helpful = attempt.get('was_helpful', True)
            
            # Calculate complexity score based on hint level and content length
            complexity = (hint_level / 5.0) * (len(hint_content) / 500.0)  # Normalize
            
            if was_helpful:
                complexity_scores.append(complexity)
        
        if not complexity_scores:
            return 0.5
        
        avg_complexity = np.mean(complexity_scores)
        self.logger.info(f"✅ Cognitive load preference: {avg_complexity:.2f}")
        return avg_complexity
    
    def analyze_performance_patterns(self, user_attempts: List[Dict]) -> Dict[str, Any]:
        """Analyze user's performance patterns for better personalization"""
        self.logger.info("📊 Analyzing performance patterns...")
        
        if not user_attempts:
            return {
                'success_rate': 0.5,
                'avg_attempts_per_problem': 3,
                'time_to_success': 300,  # seconds
                'difficulty_preference': 3,
                'consistency_score': 0.5
            }
        
        # Calculate success rate
        successful_attempts = sum(1 for a in user_attempts if a.get('success', False))
        success_rate = successful_attempts / len(user_attempts)
        
        # Calculate average attempts per problem
        problem_ids = set(a.get('problem_id') for a in user_attempts)
        avg_attempts_per_problem = len(user_attempts) / len(problem_ids) if problem_ids else 3
        
        # Calculate time to success
        successful_times = []
        for attempt in user_attempts:
            if attempt.get('success', False):
                time_taken = attempt.get('time_taken', 300)
                successful_times.append(time_taken)
        
        avg_time_to_success = np.mean(successful_times) if successful_times else 300
        
        # Calculate difficulty preference
        difficulty_scores = []
        for attempt in user_attempts:
            problem_difficulty = attempt.get('problem_difficulty', 3)
            was_helpful = attempt.get('was_helpful', True)
            if was_helpful:
                difficulty_scores.append(problem_difficulty)
        
        difficulty_preference = np.mean(difficulty_scores) if difficulty_scores else 3
        
        # Calculate consistency score
        success_sequence = [a.get('success', False) for a in user_attempts]
        consistency_score = self._calculate_consistency(success_sequence)
        
        patterns = {
            'success_rate': success_rate,
            'avg_attempts_per_problem': avg_attempts_per_problem,
            'time_to_success': avg_time_to_success,
            'difficulty_preference': difficulty_preference,
            'consistency_score': consistency_score
        }
        
        self.logger.info(f"✅ Performance patterns analyzed: {patterns}")
        return patterns
    
    def _calculate_consistency(self, success_sequence: List[bool]) -> float:
        """Calculate how consistent the user's performance is"""
        if len(success_sequence) < 2:
            return 0.5
        
        # Calculate variance in success pattern
        success_rates = []
        window_size = min(5, len(success_sequence) // 2)
        
        for i in range(0, len(success_sequence) - window_size + 1, window_size):
            window = success_sequence[i:i + window_size]
            success_rates.append(sum(window) / len(window))
        
        if len(success_rates) < 2:
            return 0.5
        
        # Lower variance = higher consistency
        variance = np.var(success_rates)
        consistency = max(0, 1 - variance)
        return consistency
    
    def generate_personalized_hint_parameters(self, user_profile: UserProfile, 
                                           current_context: Dict) -> Dict[str, Any]:
        """Generate personalized hint parameters based on user profile"""
        self.logger.info("🎯 Generating personalized hint parameters...")
        
        # Base parameters
        base_params = {
            'hint_length': 200,
            'detail_level': 0.5,
            'include_examples': False,
            'include_visual_aids': False,
            'step_by_step': False,
            'cognitive_load': 0.5
        }
        
        # Adjust based on learning style
        if user_profile.learning_style == LearningStyle.VISUAL:
            base_params['include_visual_aids'] = True
            base_params['hint_length'] += 50
        elif user_profile.learning_style == LearningStyle.AUDITORY:
            base_params['step_by_step'] = True
            base_params['hint_length'] += 100
        elif user_profile.learning_style == LearningStyle.KINESTHETIC:
            base_params['include_examples'] = True
            base_params['hint_length'] += 75
        elif user_profile.learning_style == LearningStyle.READ_WRITE:
            base_params['detail_level'] += 0.2
            base_params['hint_length'] += 25
        
        # Adjust based on cognitive load preference
        base_params['cognitive_load'] = user_profile.cognitive_load_preference
        base_params['detail_level'] = user_profile.cognitive_load_preference
        
        # Adjust based on success rate
        if user_profile.success_rate < 0.3:
            # Struggling user - provide more support
            base_params['hint_length'] += 100
            base_params['include_examples'] = True
            base_params['step_by_step'] = True
        elif user_profile.success_rate > 0.8:
            # High performer - provide concise hints
            base_params['hint_length'] = max(100, base_params['hint_length'] - 50)
            base_params['detail_level'] = max(0.3, base_params['detail_level'] - 0.2)
        
        # Adjust based on problem solving speed
        if user_profile.problem_solving_speed > 600:  # Slow solver
            base_params['step_by_step'] = True
            base_params['hint_length'] += 50
        
        self.logger.info(f"✅ Personalized parameters: {base_params}")
        return base_params
    
    def create_user_profile(self, user_id: int, user_attempts: List[Dict]) -> UserProfile:
        """Create a comprehensive user profile"""
        self.logger.info(f"👤 Creating user profile for user {user_id}...")
        
        learning_style = self.analyze_learning_style(user_attempts)
        cognitive_load = self.calculate_cognitive_load_preference(user_attempts)
        performance_patterns = self.analyze_performance_patterns(user_attempts)
        
        profile = UserProfile(
            user_id=user_id,
            learning_style=learning_style,
            preferred_hint_length=int(200 + (cognitive_load * 200)),
            cognitive_load_preference=cognitive_load,
            problem_solving_speed=performance_patterns['time_to_success'],
            success_rate=performance_patterns['success_rate'],
            preferred_examples=cognitive_load > 0.6,
            preferred_visual_aids=learning_style == LearningStyle.VISUAL,
            preferred_step_by_step=learning_style == LearningStyle.AUDITORY
        )
        
        self.logger.info(f"✅ User profile created: {profile}")
        return profile 