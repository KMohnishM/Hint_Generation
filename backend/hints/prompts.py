def get_hint_prompt(
    problem_description: str,
    user_code: str,
    previous_hints: list,
    hint_level: int,
    user_progress: dict,
    hint_type: str = 'conceptual'
) -> str:
    """
    Constructs the prompt for hint generation with context about user progress
    """
    return f"""
    Problem Description: {problem_description}
    
    User's Current Code:
    {user_code}
    
    User Progress:
    - Total Attempts: {user_progress['attempts_count']}
    - Failed Attempts: {user_progress['failed_attempts_count']}
    - Current Hint Level: {user_progress['current_hint_level']}
    - Time Since Last Attempt: {user_progress['time_since_last_attempt']} seconds
    
    Previous Hints Given:
    {previous_hints}
    
    Current Hint Level: {hint_level}
    Hint Type: {hint_type}
    
    Please generate a hint that:
    1. Is non-revealing (doesn't give away the solution)
    2. Is appropriate for hint level {hint_level} and type {hint_type}
    3. Builds upon previous hints and user's progress
    4. Guides the user to think about the problem
    5. Is specific to their current code and approach
    6. Considers their previous attempts and failures
    7. Provides pedagogical value by encouraging problem-solving skills
    
    The hint should be:
    - More conceptual for early levels
    - More specific for higher levels
    - Focused on the current hint type
    - Aligned with the user's learning progress
    """

def get_evaluation_prompt(
    hint_content: str,
    problem_description: str,
    user_code: str,
    user_progress: dict,
    previous_hints: list
) -> str:
    """
    Constructs the prompt for comprehensive hint evaluation
    """
    return f"""
    Problem Description: {problem_description}
    
    User's Code:
    {user_code}
    
    User Progress:
    - Total Attempts: {user_progress['attempts_count']}
    - Failed Attempts: {user_progress['failed_attempts_count']}
    - Current Hint Level: {user_progress['current_hint_level']}
    - Time Since Last Attempt: {user_progress['time_since_last_attempt']} seconds
    
    Previous Hints:
    {previous_hints}
    
    Hint to Evaluate:
    {hint_content}
    
    Please evaluate this hint on the following criteria:
    1. Safety (0-1): How well does it avoid revealing the solution?
    2. Helpfulness (0-1): How useful is it for guiding the user?
    3. Quality (0-1): How well-written and clear is it?
    4. Progress Alignment (0-1): How well does it match the user's current progress?
    5. Pedagogical Value (0-1): How well does it encourage learning and problem-solving?
    
    For each criterion, provide:
    - A score between 0 and 1
    - A brief explanation of the score
    - Suggestions for improvement if score is below 0.7
    """

def get_auto_trigger_prompt(
    problem_description: str,
    user_code: str,
    user_progress: dict,
    last_attempt: dict
) -> str:
    """
    Constructs the prompt for determining if a hint should be auto-triggered
    """
    return f"""
    Problem Description: {problem_description}
    
    User's Current Code:
    {user_code}
    
    User Progress:
    - Total Attempts: {user_progress['attempts_count']}
    - Failed Attempts: {user_progress['failed_attempts_count']}
    - Current Hint Level: {user_progress['current_hint_level']}
    - Time Since Last Attempt: {user_progress['time_since_last_attempt']} seconds
    
    Last Attempt:
    - Status: {last_attempt['status']}
    - Error Message: {last_attempt['error_message']}
    - Test Cases Passed: {last_attempt['test_cases_passed']}/{last_attempt['total_test_cases']}
    
    Please analyze if the user needs a hint based on:
    1. Time since last activity
    2. Number of failed attempts
    3. Error patterns in the code
    4. Test case failures
    5. Code complexity and approach
    
    Provide:
    1. A decision (yes/no) on whether to trigger a hint
    2. The reason for the decision
    3. The recommended hint type (conceptual/approach/implementation/debug)
    4. The recommended hint level
    """ 