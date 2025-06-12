# Personalized Contextual Hint Generation System

A Django-based system for generating intelligent, contextual hints for coding problems. The system uses OpenRouter's API to generate hints based on the problem statement, user's code, and their progress.

## Features

- Intelligent hint generation based on problem context and user code
- Real-time hint delivery
- User progress tracking
- Tiered hint system
- Automatic hint triggering when users are stuck
- Hint quality evaluation

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd hint-system
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenRouter API key
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## API Testing with Postman

### 1. Request a Hint

**Endpoint:** `POST http://127.0.0.1:8000/api/hints/request_hint/`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
    "user_id": 123,
    "problem_id": 1,
    "user_code": "def twoSum(nums, target):\n    # Your code here",
    "problem_data": {
        "title": "Two Sum",
        "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
    }
}
```

**Response:**
```json
{
    "hint": {
        "id": 1,
        "content": "Consider using a hash map to store the numbers you've seen...",
        "level": 1,
        "type": "conceptual"
    },
    "evaluation": {
        "safety_score": 0.95,
        "helpfulness_score": 0.85,
        "quality_score": 0.90,
        "progress_alignment_score": 0.88,
        "pedagogical_value_score": 0.92
    },
    "attempt_id": 1,
    "user_progress": {
        "attempts_count": 1,
        "failed_attempts_count": 0,
        "current_hint_level": 2,
        "is_stuck": false
    }
}
```

### 2. Check Auto-Trigger

**Endpoint:** `POST http://127.0.0.1:8000/api/hints/check_auto_trigger/`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
    "user_id": 123,
    "problem_id": 1,
    "user_code": "def twoSum(nums, target):\n    # Your code here"
}
```

**Response (if hint should be triggered):**
```json
{
    "should_trigger": true,
    "hint": {
        "id": 2,
        "content": "Try using a hash map to store the numbers...",
        "level": 2,
        "type": "approach"
    },
    "evaluation": {
        "safety_score": 0.95,
        "helpfulness_score": 0.85,
        "quality_score": 0.90,
        "progress_alignment_score": 0.88,
        "pedagogical_value_score": 0.92
    },
    "attempt_id": 2,
    "user_progress": {
        "attempts_count": 2,
        "failed_attempts_count": 1,
        "current_hint_level": 3,
        "is_stuck": true
    }
}
```

**Response (if hint should not be triggered):**
```json
{
    "should_trigger": false,
    "user_progress": {
        "attempts_count": 1,
        "failed_attempts_count": 0,
        "current_hint_level": 1,
        "is_stuck": false
    }
}
```

## Testing Workflow

1. **First Request:**
   - Send problem data with the first request
   - System will create a new problem record
   - Returns first hint and evaluation

2. **Subsequent Requests:**
   - Only need to send problem_id (no need for problem data)
   - System will use existing problem
   - Returns next hint in sequence

3. **Auto-Trigger:**
   - System automatically checks if user is stuck
   - Triggers hint if user has been inactive for 5 minutes and has 3+ failed attempts
   - Returns hint with evaluation if triggered

## Error Handling

- **400 Bad Request:** Missing required fields
- **404 Not Found:** Problem not found and no problem data provided

## Development

To modify the system:

1. **Add New Hint Types:**
   - Update `HINT_TYPES` in `hints/models.py`
   - Add corresponding prompt templates in `hints/prompts.py`

2. **Modify Hint Generation:**
   - Update prompt templates in `hints/prompts.py`
   - Adjust evaluation criteria in `hints/services.py`

3. **Change Auto-Trigger Logic:**
   - Modify `is_stuck()` method in `UserProgress` model
   - Update thresholds in `hints/views.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 