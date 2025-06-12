import os
import requests
from django.conf import settings
from typing import Dict, Any, Optional, List, Tuple
from .prompts import get_hint_prompt, get_evaluation_prompt, get_auto_trigger_prompt

class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _make_api_call(self, prompt: str) -> str:
        """Make API call to OpenRouter"""
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "anthropic/claude-3-opus-20240229",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
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
        current_criterion = None
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                current_criterion = line.split('.')[1].strip().lower()
            elif current_criterion and ':' in line:
                try:
                    score = float(line.split(':')[1].strip())
                    scores[current_criterion] = score
                except (ValueError, IndexError):
                    continue
        
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