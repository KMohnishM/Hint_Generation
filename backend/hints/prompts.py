import logging

logger = logging.getLogger(__name__)

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
    # Log previous hints being sent to LLM
    logger.info("\n=== Previous Hints Being Sent to LLM ===")
    for i, hint in enumerate(previous_hints, 1):
        logger.info(f"\nPrevious Hint {i}:")
        logger.info(f"Content: {hint}")
    logger.info("-" * 50)

    # Log user progress being sent to LLM
    logger.info("\n=== User Progress Being Sent to LLM ===")
    logger.info(f"Total Attempts: {user_progress['attempts_count']}")
    logger.info(f"Failed Attempts: {user_progress['failed_attempts_count']}")
    logger.info(f"Current Hint Level: {user_progress['current_hint_level']}")
    logger.info(f"Time Since Last Attempt: {user_progress['time_since_last_attempt']} seconds")
    logger.info(f"Is Stuck: {user_progress['is_stuck']}")
    logger.info("-" * 50)

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
    # Log what's being sent to LLM for evaluation
    logger.info("\n=== Evaluation Request Being Sent to LLM ===")
    logger.info(f"Hint Content: {hint_content}")
    logger.info(f"User Code: {user_code}")
    logger.info(f"User Progress: {user_progress}")
    logger.info(f"Previous Hints: {previous_hints}")
    logger.info("-" * 50)

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
    
    Please evaluate this hint and provide scores in the following format:
    
    safety_score: [score between 0 and 1]
    helpfulness_score: [score between 0 and 1]
    quality_score: [score between 0 and 1]
    progress_alignment_score: [score between 0 and 1]
    pedagogical_value_score: [score between 0 and 1]
    
    For each score, provide a number between 0 and 1, where:
    - 0 means completely ineffective
    - 1 means perfect effectiveness
    
    Example response format:
    safety_score: 0.8
    helpfulness_score: 0.7
    quality_score: 0.9
    progress_alignment_score: 0.6
    pedagogical_value_score: 0.8
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
    # Log what's being sent to LLM for auto-trigger decision
    logger.info("\n=== Auto-Trigger Decision Being Sent to LLM ===")
    logger.info(f"User Code: {user_code}")
    logger.info(f"User Progress: {user_progress}")
    logger.info(f"Last Attempt: {last_attempt}")
    logger.info("-" * 50)

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