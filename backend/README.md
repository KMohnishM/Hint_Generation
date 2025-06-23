# Hint Generation System

> **Note:** This is a production-only, minimal codebase. All development, test, and legacy files have been removed for clarity and maintainability. The main workflow is orchestrated by `hints/hint_chain.py` and exposed via `hints/views.py`.

A Django-based backend system for generating adaptive hints for programming problems. The system uses LLMs (Large Language Models) to generate context-aware hints based on user progress and code attempts.

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

1. **Conceptual (Level 1)** – Basic understanding, core concepts
2. **Approach (Level 2)** – Problem-solving strategies, algorithms
3. **Implementation (Level 3)** – Code structure, patterns, syntax
4. **Debug (Level 4)** – Logical/code errors, fixes
5. **Solution (Level 5)** – Nearly complete solution, for stuck users

### Hint Types

- **Conceptual**: Explains underlying concepts
- **Approach**: Suggests solution strategies
- **Implementation**: Focuses on code structure
- **Debug**: Identifies specific issues

### Progress Tracking

- **Attempts Count**: Total code submissions
- **Failed Attempts**: Incorrect submissions
- **Current Hint Level**: User's progression level
- **Time Since Last Activity**: User inactivity
- **User Stuck Detection**: Identifies struggling users

### Hint Evaluation

Each generated hint is evaluated on:

- **Safety Score**: Does not reveal too much
- **Helpfulness Score**: Effectiveness
- **Quality Score**: Clarity and precision
- **Progress Alignment**: Matches user's level
- **Pedagogical Value**: Educational effectiveness

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Create a `.env` file in the backend directory**

   ```bash
   touch .env  # On Windows: type nul > .env
   ```
4. **Add the following to your `.env` file:**

   ```env
   # OpenRouter API Configuration
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # (Optional, if using TogetherAI or HuggingFace)
   TOGETHER_API_KEY=your_togetherai_or_huggingface_key_here

   # Django Configuration
   DEBUG=True
   SECRET_KEY=your_django_secret_key_here

   # LangSmith / LangChain Tracing Configuration
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   LANGSMITH_PROJECT=hg
   LANGSMITH_TRACING_V2=true
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com

   # Compatibility/Alternative variable names (sometimes required)
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=hg
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   ```
5. **Run database migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. **Start the Django development server**

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
    "problem_data": {               // Required if problem doesn't exist
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

1. **Attempt Evaluation**: User submits code, system evaluates correctness, identifies issues, determines if hint is needed
2. **Progress Tracking**: Updates attempt counts, failed attempts, user activity, detects if user is stuck
3. **Hint Level Determination**: Based on progress, failed attempts, inactivity, issues, current level
4. **Hint Type Selection**: Conceptual, Approach, Implementation, Debug—based on user need
5. **Hint Generation**: LLM generates context-aware hints, considers previous hints, adapts to user
6. **Hint Evaluation**: Evaluates hint quality, safety, helpfulness, alignment, pedagogical value

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
