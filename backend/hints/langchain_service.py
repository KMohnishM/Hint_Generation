import os
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from django.conf import settings
from .prompts import get_hint_prompt, get_evaluation_prompt, get_auto_trigger_prompt

# Configure detailed logging
logger = logging.getLogger(__name__)

# Pydantic models for structured outputs
class AttemptEvaluation(BaseModel):
    success: bool = Field(description="Whether the attempt was successful")
    reason: str = Field(description="Brief explanation of the evaluation")
    complexity: str = Field(description="Time and space complexity analysis")
    edge_cases: List[str] = Field(description="List of edge cases handled or missed")
    code_quality: str = Field(description="Assessment of code quality")
    suggestions: List[str] = Field(description="Specific suggestions for improvement")

class HintEvaluation(BaseModel):
    safety_score: float = Field(description="Safety score between 0 and 1")
    helpfulness_score: float = Field(description="Helpfulness score between 0 and 1")
    quality_score: float = Field(description="Quality score between 0 and 1")
    progress_alignment_score: float = Field(description="Progress alignment score between 0 and 1")
    pedagogical_value_score: float = Field(description="Pedagogical value score between 0 and 1")

class AutoTriggerDecision(BaseModel):
    should_trigger: bool = Field(description="Whether to trigger a hint")
    reason: str = Field(description="Reason for the decision")
    hint_type: str = Field(description="Recommended hint type")
    hint_level: int = Field(description="Recommended hint level")

class LangChainService:
    def __init__(self):
        logger.info("🚀 Initializing LangChainService...")
        
        self.api_key = settings.OPENROUTER_API_KEY
        self.langsmith_api_key = settings.LANGSMITH_API_KEY
        
        logger.info(f"📋 Configuration:")
        logger.info(f"   - OpenRouter API Key: {'✅ Set' if self.api_key else '❌ Not set'}")
        logger.info(f"   - LangSmith API Key: {'✅ Set' if self.langsmith_api_key else '❌ Not set'}")
        
        # Configure LangSmith if available
        if self.langsmith_api_key:
            logger.info("🔧 Configuring LangSmith environment variables...")
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGSMITH_TRACING_V2)
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
            
            logger.info(f"   - LangSmith Project: {settings.LANGSMITH_PROJECT}")
            logger.info(f"   - LangSmith Tracing: {settings.LANGSMITH_TRACING_V2}")
            logger.info(f"   - LangSmith Endpoint: {settings.LANGSMITH_ENDPOINT}")
        else:
            logger.warning("⚠️  LangSmith API key not set - no tracing will be available")
        
        # Initialize LLM using ChatOpenAI with OpenRouter base
        self.llm = None
        try:
            logger.info("🤖 Attempting to initialize ChatOpenAI with OpenRouter...")
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                openai_api_key=self.api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.7
            )
            logger.info("✅ LangChain OpenAI client initialized successfully with OpenRouter base URL.")
        except ImportError as e:
            logger.error(f"❌ langchain_openai not installed: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChatOpenAI: {e}")
        
        # Simple in-memory conversation history (not per-user)
        self.memory = []
        logger.info("✅ LangChainService initialization completed.")

    def _make_api_call(self, prompt: str) -> str:
        """Make API call using LangChain LLM"""
        try:
            logger.debug("Making API call to OpenRouter via LangChain")
            if self.llm:
                response = self.llm.invoke(prompt)
                return response.content
            else:
                raise Exception("LLM not initialized")
        except Exception as e:
            logger.error(f"LangChain API call failed: {str(e)}")
            raise Exception(f"LangChain API call failed: {str(e)}")

    def generate_hint(
        self,
        problem_description: str,
        user_code: str,
        previous_hints: List[Dict],
        hint_level: int,
        user_progress: Dict,
        hint_type: str = 'conceptual'
    ) -> str:
        """Generate a hint using LangChain with conversation memory and AI-powered prompts"""
        
        logger.info("💡 Starting hint generation...")
        logger.info(f"   - Hint Level: {hint_level}")
        logger.info(f"   - Hint Type: {hint_type}")
        logger.info(f"   - User Progress: {json.dumps(user_progress, indent=2)}")
        logger.info(f"   - Previous Hints Count: {len(previous_hints)}")
        
        # Log previous hints
        if previous_hints:
            logger.info("📝 Previous hints:")
            for i, hint in enumerate(previous_hints, 1):
                if isinstance(hint, dict):
                    logger.info(f"   Hint {i}: {hint.get('content', str(hint))[:100]}...")
                else:
                    logger.info(f"   Hint {i}: {str(hint)[:100]}...")
        
        # Use the sophisticated prompt from the old service
        prompt = get_hint_prompt(
            problem_description=problem_description,
            user_code=user_code,
            previous_hints=previous_hints,
            hint_level=hint_level,
            user_progress=user_progress,
            hint_type=hint_type
        )
        
        logger.info("📤 Sending prompt to LLM...")
        logger.info(f"   - Prompt length: {len(prompt)} characters")
        logger.info(f"   - LLM available: {'✅ Yes' if self.llm else '❌ No'}")
        
        if self.llm:
            try:
                logger.info("🔄 Making API call to OpenRouter...")
                response = self._make_api_call(prompt)
                logger.info("✅ LLM response received successfully")
                logger.info(f"   - Response length: {len(response)} characters")
                logger.info(f"   - Response preview: {response[:100]}...")
                
                # Log the full response for debugging
                logger.debug(f"📄 Full LLM Response: {response}")
                
                return response
            except Exception as e:
                logger.error(f"❌ LLM call failed: {e}")
                logger.error(f"   - Error type: {type(e).__name__}")
                logger.error(f"   - Error details: {str(e)}")
                fallback_hint = self._get_default_hint(hint_level, hint_type)
                logger.info(f"🔄 Using fallback hint: {fallback_hint}")
                return fallback_hint
        else:
            logger.warning("⚠️  No LLM available, using default hint")
            fallback_hint = self._get_default_hint(hint_level, hint_type)
            logger.info(f"🔄 Using default hint: {fallback_hint}")
            return fallback_hint

    def _get_default_hint(self, hint_level: int, hint_type: str) -> str:
        logger.info(f"🎯 Generating default hint for level {hint_level}, type {hint_type}")
        
        if hint_type == "conceptual":
            if hint_level == 1:
                hint = "Think about what data structure would help you efficiently find pairs of numbers that sum to the target."
            elif hint_level == 2:
                hint = "Consider using a hash map to store the numbers you've seen so far."
            else:
                hint = "A hash map allows you to check if a complement exists in O(1) time."
        elif hint_type == "approach":
            hint = "Try iterating through the array once, storing each number in a hash map and checking if its complement exists."
        elif hint_type == "implementation":
            hint = "Initialize an empty hash map, then for each number, check if (target - current_number) exists in the map."
        else:  # debug
            hint = "Make sure you're checking for the complement (target - current_number) before adding the current number to the map."
        
        logger.info(f"   - Default hint: {hint}")
        return hint

    def evaluate_hint(
        self,
        hint_content: str,
        problem_description: str,
        user_code: str,
        user_progress: Dict,
        previous_hints: List[Dict]
    ) -> Dict[str, float]:
        """Evaluate a hint's quality and effectiveness using AI-powered analysis"""
        logger.info("📊 Starting hint evaluation...")
        logger.info(f"   - Hint content length: {len(hint_content)} characters")
        logger.info(f"   - User code length: {len(user_code)} characters")
        
        # Use the sophisticated evaluation prompt from the old service
        prompt = get_evaluation_prompt(
            hint_content=hint_content,
            problem_description=problem_description,
            user_code=user_code,
            user_progress=user_progress,
            previous_hints=previous_hints
        )
        
        try:
            response = self._make_api_call(prompt)
            logger.info("✅ Hint evaluation response received")
            
            # Parse the evaluation response (same logic as old service)
            scores = {}
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    try:
                        score = float(value.strip())
                        if 0 <= score <= 1:  # Ensure score is between 0 and 1
                            scores[key] = score
                    except (ValueError, IndexError):
                        continue
            
            # Ensure all required scores are present
            required_scores = [
                'safety_score',
                'helpfulness_score',
                'quality_score',
                'progress_alignment_score',
                'pedagogical_value_score'
            ]
            
            # Set default score of 0.0 for any missing scores
            for score in required_scores:
                if score not in scores:
                    scores[score] = 0.0
            
            logger.info("📈 Evaluation scores:")
            for key, value in scores.items():
                logger.info(f"   - {key}: {value}")
            
            return scores
            
        except Exception as e:
            logger.error(f"❌ Hint evaluation failed: {e}")
            # Return default scores on failure
            default_scores = {
                'safety_score': 0.8,
                'helpfulness_score': 0.7,
                'quality_score': 0.8,
                'progress_alignment_score': 0.7,
                'pedagogical_value_score': 0.8
            }
            logger.info("🔄 Using default evaluation scores")
            return default_scores

    def evaluate_attempt(
        self,
        problem_description: str,
        user_code: str,
        expected_output: str = None
    ) -> Dict[str, Any]:
        """Evaluate if the user's attempt was successful using AI-powered analysis"""
        logger.info("🔍 Starting attempt evaluation...")
        logger.info(f"   - Problem description length: {len(problem_description)} characters")
        logger.info(f"   - User code length: {len(user_code)} characters")
        logger.info(f"   - Expected output provided: {'✅ Yes' if expected_output else '❌ No'}")
        
        # Use the sophisticated evaluation prompt from the old service
        prompt = f"""
        Problem Description: {problem_description}
        
        User's Code:
        {user_code}
        
        Please analyze if this code would solve the problem correctly. Consider:
        1. Logic correctness
        2. Edge cases
        3. Time and space complexity
        4. Code quality
        
        Respond in the following format:
        success: [true/false]
        reason: [brief explanation]
        complexity: [time and space complexity]
        edge_cases: [list of edge cases handled or missed]
        
        Example response:
        success: false
        reason: The code doesn't handle the case where no solution exists
        complexity: O(n) time, O(1) space
        edge_cases: Missing empty array, missing no-solution case
        """
        
        try:
            response = self._make_api_call(prompt)
            logger.info("✅ Attempt evaluation response received")
            
            # Parse the response (same logic as old service)
            result = {
                'success': False,
                'reason': '',
                'complexity': '',
                'edge_cases': []
            }
            
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'success':
                        result['success'] = value.lower() == 'true'
                    elif key == 'reason':
                        result['reason'] = value
                    elif key == 'complexity':
                        result['complexity'] = value
                    elif key == 'edge_cases':
                        result['edge_cases'] = [case.strip() for case in value.split(',')]
            
            logger.info("📋 Evaluation results:")
            for key, value in result.items():
                if isinstance(value, list):
                    logger.info(f"   - {key}: {', '.join(value)}")
                else:
                    logger.info(f"   - {key}: {value}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Attempt evaluation failed: {e}")
            # Return default evaluation on failure
            default_evaluation = {
                'success': False,
                'reason': 'Evaluation failed - code may be incomplete',
                'complexity': 'O(1) time, O(1) space',
                'edge_cases': ['Empty array', 'No solution case'],
                'code_quality': 'Basic structure present',
                'suggestions': ['Complete the implementation', 'Add edge case handling']
            }
            logger.info("🔄 Using default evaluation")
            return default_evaluation

    def should_trigger_hint(
        self,
        problem_description: str,
        user_code: str,
        user_progress: Dict,
        last_attempt: Dict
    ) -> Tuple[bool, str, str, int]:
        """Determine if a hint should be auto-triggered using AI-powered analysis"""
        logger.info("🤖 Starting auto-trigger decision...")
        logger.info(f"   - User progress: {json.dumps(user_progress, indent=2)}")
        logger.info(f"   - Last attempt: {json.dumps(last_attempt, indent=2)}")
        
        # Use the sophisticated auto-trigger prompt from the old service
        prompt = get_auto_trigger_prompt(
            problem_description=problem_description,
            user_code=user_code,
            user_progress=user_progress,
            last_attempt=last_attempt
        )
        
        try:
            response = self._make_api_call(prompt)
            logger.info("✅ Auto-trigger decision response received")
            
            # Parse the response (same logic as old service)
            lines = response.split('\n')
            should_trigger = False
            reason = ""
            hint_type = "conceptual"
            hint_level = 1
            
            for line in lines:
                line = line.strip().lower()
                if "decision:" in line:
                    should_trigger = "yes" in line
                elif "reason:" in line:
                    reason = line.split("reason:")[1].strip()
                elif "hint type:" in line:
                    hint_type = line.split("hint type:")[1].strip()
                elif "hint level:" in line:
                    try:
                        hint_level = int(line.split("hint level:")[1].strip())
                    except (ValueError, IndexError):
                        hint_level = 1
            
            logger.info("🎯 Auto-trigger decision:")
            logger.info(f"   - Should trigger: {'✅ Yes' if should_trigger else '❌ No'}")
            logger.info(f"   - Reason: {reason}")
            logger.info(f"   - Hint type: {hint_type}")
            logger.info(f"   - Hint level: {hint_level}")
            
            return (should_trigger, reason, hint_type, hint_level)
            
        except Exception as e:
            logger.error(f"❌ Auto-trigger decision failed: {e}")
            # Fallback to simple heuristic
            should_trigger = user_progress.get('failed_attempts_count', 0) >= 3
            reason = "Multiple failed attempts" if should_trigger else "User making progress"
            hint_type = "debug" if should_trigger else "conceptual"
            hint_level = min(user_progress.get('current_hint_level', 1) + 1, 5)
            
            logger.info("🔄 Using fallback auto-trigger decision:")
            logger.info(f"   - Should trigger: {'✅ Yes' if should_trigger else '❌ No'}")
            logger.info(f"   - Reason: {reason}")
            logger.info(f"   - Hint type: {hint_type}")
            logger.info(f"   - Hint level: {hint_level}")
            
            return (should_trigger, reason, hint_type, hint_level)

    def clear_memory(self, user_id: int, problem_id: int):
        logger.info(f"🧹 Clearing memory for user {user_id} on problem {problem_id}")
        self.memory = []
        logger.info("✅ Memory cleared successfully") 