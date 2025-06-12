# Hint Generation System

A Django-based backend system for generating adaptive hints for programming problems. The system uses LLM (Large Language Model) to generate context-aware hints based on user progress and code attempts.

## Features

### Adaptive Hint Generation
The system generates hints based on multiple factors:
- **User's Current Progress**: Tracks how far the user has progressed in solving the problem
- **Previous Attempts**: Analyzes past code submissions and their outcomes
- **Code Evaluation**: Assesses the correctness and quality of submitted code
- **Hint Level Progression**: Adapts hint complexity based on user's current level
- **Specific Issues**: Identifies and addresses particular problems in the code

### Hint Levels
The system uses a 5-level progression system:

1. **Conceptual (Level 1)**
   - Focuses on basic problem understanding
   - Explains core concepts and requirements
   - Helps users grasp the problem's fundamentals

2. **Approach (Level 2)**
   - Provides problem-solving strategies
   - Suggests algorithms or methods
   - Guides users in planning their solution

3. **Implementation (Level 3)**
   - Helps with code structure and organization
   - Provides guidance on coding patterns
   - Assists with syntax and best practices

4. **Debug (Level 4)**
   - Addresses specific issues in the code
   - Points out logical errors
   - Suggests fixes for implementation problems

5. **Solution (Level 5)**
   - Provides almost complete solution guidance
   - Used when user is stuck for extended periods
   - Focuses on getting users unstuck

### Hint Types
Each hint is categorized into one of four types:

- **Conceptual**
  - Explains underlying concepts
  - Clarifies problem requirements
  - Helps understand the problem domain

- **Approach**
  - Suggests solution strategies
  - Provides algorithm insights
  - Guides problem-solving methodology

- **Implementation**
  - Focuses on code structure
  - Provides coding patterns
  - Helps with syntax and organization

- **Debug**
  - Identifies specific issues
  - Suggests fixes
  - Addresses error patterns

### Progress Tracking
The system maintains detailed progress metrics:

- **Attempts Count**: Total number of code submissions
- **Failed Attempts**: Number of incorrect submissions
- **Current Hint Level**: User's current progression level
- **Time Since Last Activity**: Duration of user inactivity
- **User Stuck Detection**: Identifies when users are struggling

### Hint Evaluation
Each generated hint is evaluated on five criteria:

- **Safety Score**: Measures if the hint reveals too much of the solution
- **Helpfulness Score**: Assesses the hint's effectiveness in guiding the user
- **Quality Score**: Evaluates the clarity and precision of the hint
- **Progress Alignment**: Checks if the hint matches the user's current level
- **Pedagogical Value**: Measures the hint's educational effectiveness

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```bash
   touch .env  # On Windows: type nul > .env
   ```

4. Add the following to your `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   DEBUG=True
   SECRET_KEY=your_django_secret_key
   ```

5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Request Hint
```
POST /api/hints/request_hint/
```
Request body:
```json
{
    "user_id": "integer",          // Unique identifier for the user
    "problem_id": "integer",       // Unique identifier for the problem
    "user_code": "string",         // The code submitted by the user
    "problem_data": {              // Required if problem doesn't exist
        "title": "string",         // Problem title
        "description": "string"    // Problem description
    }
}
```

Response:
```json
{
    "status": "failed",            // 'success' or 'failed'
    "hint": {
        "id": "integer",           // Unique identifier for the hint
        "content": "string",       // The hint text
        "level": "integer",        // Hint level (1-5)
        "type": "string"           // Hint type (conceptual/approach/implementation/debug)
    },
    "evaluation": {
        "safety_score": "float",           // How much of the solution is revealed (0-1)
        "helpfulness_score": "float",      // How helpful the hint is (0-1)
        "quality_score": "float",          // Overall quality of the hint (0-1)
        "progress_alignment_score": "float", // How well it matches user's level (0-1)
        "pedagogical_value_score": "float"  // Educational value (0-1)
    },
    "attempt_id": "integer",       // Unique identifier for this attempt
    "attempt_evaluation": {
        "success": "boolean",      // Whether the code is correct
        "reason": "string",        // Explanation of the evaluation
        "complexity": "string",    // Time and space complexity
        "edge_cases": ["string"]   // List of edge cases handled/missed
    },
    "user_progress": {
        "attempts_count": "integer",        // Total attempts made
        "failed_attempts_count": "integer", // Total failed attempts
        "current_hint_level": "integer",    // Current hint level (1-5)
        "is_stuck": "boolean",             // Whether user is stuck
        "time_since_last_attempt": "float"  // Seconds since last attempt
    }
}
```

## Models

### Problem
- `id`: AutoField (Primary Key)
- `title`: CharField (Problem Title)
- `description`: TextField (Detailed Problem Description)
- `difficulty`: CharField (Easy/Medium/Hard)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

### UserProgress
- `user_id`: IntegerField (User Identifier)
- `problem`: ForeignKey to Problem (Related Problem)
- `last_activity`: DateTimeField (Last User Activity)
- `attempts_count`: IntegerField (Total Attempts)
- `failed_attempts_count`: IntegerField (Failed Attempts)
- `current_hint_level`: IntegerField (Current Hint Level)

### Attempt
- `user_id`: IntegerField (User Identifier)
- `problem`: ForeignKey to Problem (Related Problem)
- `code`: TextField (Submitted Code)
- `status`: CharField (Success/Failed)
- `evaluation_details`: JSONField (Detailed Evaluation)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

### Hint
- `problem`: ForeignKey to Problem (Related Problem)
- `content`: TextField (Hint Content)
- `level`: IntegerField (Hint Level 1-5)
- `hint_type`: CharField (Conceptual/Approach/Implementation/Debug)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

### HintDelivery
- `hint`: ForeignKey to Hint (Related Hint)
- `user_id`: IntegerField (User Identifier)
- `attempt`: ForeignKey to Attempt (Related Attempt)
- `is_auto_triggered`: BooleanField (Auto-Triggered Flag)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

### HintEvaluation
- `hint`: ForeignKey to Hint (Related Hint)
- `safety_score`: FloatField (Safety Score 0-1)
- `helpfulness_score`: FloatField (Helpfulness Score 0-1)
- `quality_score`: FloatField (Quality Score 0-1)
- `progress_alignment_score`: FloatField (Progress Alignment 0-1)
- `pedagogical_value_score`: FloatField (Pedagogical Value 0-1)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

## Hint Generation Process

1. **Attempt Evaluation**:
   - User submits code
   - System evaluates code correctness
   - Identifies specific issues (edge cases, complexity, logic)
   - Determines if hint is needed

2. **Progress Tracking**:
   - Updates attempt counts
   - Tracks failed attempts
   - Monitors user activity
   - Detects if user is stuck

3. **Hint Level Determination**:
   - Based on user progress
   - Failed attempts count
   - Time since last activity
   - Specific issues identified
   - Current hint level

4. **Hint Type Selection**:
   - Conceptual for basic understanding
   - Approach for problem-solving strategy
   - Implementation for code structure
   - Debug for specific issues
   - Based on identified problems

5. **Hint Generation**:
   - Uses LLM to generate context-aware hints
   - Considers previous hints
   - Adapts to user's current level
   - Focuses on specific issues
   - Ensures pedagogical value

6. **Hint Evaluation**:
   - Evaluates hint quality
   - Ensures safety and helpfulness
   - Checks progress alignment
   - Assesses pedagogical value
   - Validates against criteria

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 