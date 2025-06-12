# Hint Generation Backend

This is the backend service for the Hint Generation system, which provides intelligent hints for coding problems.

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory with the following content:
```
OPENROUTER_API_KEY=your_api_key_here
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Request a Hint
```
POST /api/hints/request_hint/
```

Request body:
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

Response:
```json
{
    "hint": {
        "id": 1,
        "content": "Hint content here...",
        "level": 1,
        "type": "conceptual"
    },
    "evaluation": {
        "safety_score": 0.8,
        "helpfulness_score": 0.7,
        "quality_score": 0.9,
        "progress_alignment_score": 0.6,
        "pedagogical_value_score": 0.8
    },
    "attempt_id": 1,
    "user_progress": {
        "attempts_count": 1,
        "failed_attempts_count": 0,
        "current_hint_level": 2,
        "is_stuck": false,
        "time_since_last_attempt": 0
    }
}
```

## Models

### Problem
- `id`: AutoField (Primary Key)
- `title`: CharField
- `description`: TextField
- `difficulty`: CharField (choices: easy, medium, hard)
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### UserProgress
- `user_id`: IntegerField
- `problem`: ForeignKey to Problem
- `last_activity`: DateTimeField
- `attempts_count`: IntegerField
- `failed_attempts_count`: IntegerField
- `current_hint_level`: IntegerField

### Attempt
- `user_id`: IntegerField
- `problem`: ForeignKey to Problem
- `code`: TextField
- `status`: CharField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### Hint
- `problem`: ForeignKey to Problem
- `content`: TextField
- `level`: IntegerField
- `hint_type`: CharField (choices: conceptual, approach, implementation, debug)
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### HintDelivery
- `hint`: ForeignKey to Hint
- `user_id`: IntegerField
- `attempt`: ForeignKey to Attempt
- `is_auto_triggered`: BooleanField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

### HintEvaluation
- `hint`: ForeignKey to Hint
- `safety_score`: FloatField
- `helpfulness_score`: FloatField
- `quality_score`: FloatField
- `progress_alignment_score`: FloatField
- `pedagogical_value_score`: FloatField
- `created_at`: DateTimeField
- `updated_at`: DateTimeField

## Dependencies

- Django >= 4.2.0
- Django REST Framework >= 3.14.0
- django-cors-headers >= 4.3.0
- channels >= 4.0.0
- psycopg2-binary >= 2.9.9
- python-dotenv >= 1.0.0
- requests >= 2.31.0
- django-filter >= 23.3

## Development

1. The backend uses OpenRouter's API for generating hints. You need to:
   - Sign up at https://openrouter.ai/
   - Get an API key
   - Add it to your `.env` file

2. The system uses the `deepseek/deepseek-r1-0528-qwen3-8b:free` model for generating hints.

3. For development, the server runs on http://localhost:8000/

## Error Handling

The API returns appropriate HTTP status codes:
- 200: Success
- 400: Bad Request (missing required fields)
- 404: Not Found (problem not found)
- 500: Internal Server Error (API or database issues)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 