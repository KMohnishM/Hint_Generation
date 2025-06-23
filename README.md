# Personalized Contextual Hint Generation System

> **Production-Ready | LangChain & LangSmith Integrated | Minimal & Modern**

A Django-based backend for generating intelligent, contextual hints for coding problems. Now fully refactored to use **LangChain** and **LangSmith** for prompt management, memory, structured output, and observability. All logic is orchestrated in `backend/hints/hint_chain.py` and exposed via `backend/hints/views.py`.

---

## 🚀 Quick Start

1. **Clone the repository and checkout the LangChain branch:**
   ```bash
   git clone https://github.com/KMohnishM/Hint_Generation.git
   cd Hint_Generation
   git checkout LangChain
   cd backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create your `.env` file in the backend directory:**
   ```bash
   cp env_template.txt .env  # Or create manually
   # Edit .env and fill in your actual keys/secrets
   ```
   Example `.env`:
   ```env
   # OpenRouter API
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # (Optional) TogetherAI/HuggingFace
   TOGETHER_API_KEY=your_togetherai_or_huggingface_key_here

   # Django
   DEBUG=True
   SECRET_KEY=your_django_secret_key_here

   # LangSmith / LangChain Tracing
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   LANGSMITH_PROJECT=hg
   LANGSMITH_TRACING_V2=true
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=hg
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   ```

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

---

## 🧠 What's New? (LangChain/LangSmith Integration)

- **No more direct OpenRouter API calls!**
- All LLM calls, prompt management, and memory are handled via LangChain.
- Observability, tracing, and experiment tracking are powered by LangSmith.
- All hint generation, evaluation, and workflow logic is in `hints/hint_chain.py`.
- Only `hints/hint_chain.py` and `hints/views.py` are used for orchestration—no legacy service files remain.
- The codebase is now minimal, production-focused, and easy to extend.

---

## 📦 API Usage

### Request a Hint
**POST** `/api/hints/request_hint/`

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
  "status": "failed",
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

### Check Auto-Trigger
**POST** `/api/hints/check_auto_trigger/`

**Body:**
```json
{
  "user_id": 123,
  "problem_id": 1,
  "user_code": "def twoSum(nums, target):\n    # Your code here"
}
```

**Response:**
```json
{
  "should_trigger": true,
  "hint": { ... },
  "evaluation": { ... },
  "attempt_id": 2,
  "user_progress": { ... }
}
```

---

## ⚙️ Error Handling
- **400 Bad Request:** Missing required fields
- **404 Not Found:** Problem not found and no problem data provided

---

## 🛠️ Development & Extending
- **Add new hint types:** Update `HINT_TYPES` in `hints/models.py` and add prompt templates in `hints/prompts.py`.
- **Modify hint generation logic:** Edit `hints/hint_chain.py` and prompt templates in `hints/prompts.py`.
- **Change auto-trigger logic:** Update logic in `hints/views.py` and `hints/hint_chain.py`.

---

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details. 
