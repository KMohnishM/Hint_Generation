import os
import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional, List, Tuple
from .prompts import get_hint_prompt, get_evaluation_prompt, get_auto_trigger_prompt

logger = logging.getLogger(__name__)

class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        logger.debug(f"OpenRouter API Key present: {bool(self.api_key)}")
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _make_api_call(self, prompt: str) -> str:
        """Make API call to OpenRouter"""
        try:
            logger.debug("Making API call to OpenRouter")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {str(e)}")
            raise Exception(f"OpenRouter API call failed: {str(e)}")

    def generate_hint(
        self,
        problem_description: str,
        user_code: str,
        previous_hints: List[Dict],
        hint_level: int,
        user_progress: Dict,
        hint_type: str = 'conceptual'
    ) -> str:
        """Generate a hint based on the problem, user code, and context"""
        prompt = get_hint_prompt(
            problem_description=problem_description,
            user_code=user_code,
            previous_hints=previous_hints,
            hint_level=hint_level,
            user_progress=user_progress,
            hint_type=hint_type
        )
        return self._make_api_call(prompt)

    def evaluate_hint(
        self,
        hint_content: str,
        problem_description: str,
        user_code: str,
        user_progress: Dict,
        previous_hints: List[Dict]
    ) -> Dict[str, float]:
        """Evaluate a hint's quality and effectiveness"""
        prompt = get_evaluation_prompt(
            hint_content=hint_content,
            problem_description=problem_description,
            user_code=user_code,
            user_progress=user_progress,
            previous_hints=previous_hints
        )
        response = self._make_api_call(prompt)
        
        # Parse the evaluation response
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
        
        # Set default score of 0.5 for any missing scores
        for score in required_scores:
            if score not in scores:
                scores[score] = 0.0
        
        return scores

    def should_trigger_hint(
        self,
        problem_description: str,
        user_code: str,
        user_progress: Dict,
        last_attempt: Dict
    ) -> Tuple[bool, str, str, int]:
        """
        Determine if a hint should be auto-triggered
        
        Returns:
            Tuple containing:
            - bool: Whether to trigger a hint
            - str: Reason for the decision
            - str: Recommended hint type
            - int: Recommended hint level
        """
        prompt = get_auto_trigger_prompt(
            problem_description=problem_description,
            user_code=user_code,
            user_progress=user_progress,
            last_attempt=last_attempt
        )
        response = self._make_api_call(prompt)
        
        # Parse the response
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
        
        return should_trigger, reason, hint_type, hint_level

    def evaluate_attempt(
        self,
        problem_description: str,
        user_code: str,
        expected_output: str = None
    ) -> Dict[str, Any]:
        """
        Evaluate if the user's attempt was successful by analyzing their code
        """
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
        
        response = self._make_api_call(prompt)
        
        # Parse the response
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
        
        return result 