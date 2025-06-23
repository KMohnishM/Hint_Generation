# Enhanced LangChain Integration: Detailed Technical Reference

---

## 1. System Overview

This system is a Django-based Personalized Contextual Hint Generation platform. It uses LangChain and OpenRouter LLMs to generate, evaluate, and deliver hints to users working on coding problems. The workflow is adaptive, tracks user progress per (user, problem) pair, avoids redundant hints, and escalates support for stuck users.

---

## 2. Data Model Reference

### **Problem**
- Represents a coding problem.
- Fields: `id`, `title`, `description`, `difficulty`, `created_at`, `updated_at`

### **UserProgress**
- Tracks a user's progress on a specific problem.
- Fields: `user_id`, `problem`, `last_activity`, `attempts_count`, `failed_attempts_count`, `current_hint_level`
- Method: `is_stuck()` — returns True if user is inactive for 5+ minutes and has 3+ failed attempts.

### **Attempt**
- Represents a user's code submission for a problem.
- Fields: `user_id`, `problem`, `code`, `status` ("success"/"failed"), `evaluation_details`, `created_at`, `updated_at`

### **Hint**
- Represents a generated hint for a problem.
- Fields: `problem`, `content`, `level`, `hint_type`, `created_at`, `updated_at`

### **HintDelivery**
- Records the delivery of a hint to a user for a specific attempt.
- Fields: `hint`, `user_id`, `attempt`, `is_auto_triggered`, `created_at`, `updated_at`

### **HintEvaluation**
- Stores LLM-evaluated scores for a hint.
- Fields: `hint`, `safety_score`, `helpfulness_score`, `quality_score`, `progress_alignment_score`, `pedagogical_value_score`, `created_at`, `updated_at`

---

## 3. Workflow: Step-by-Step

### **A. User Requests a Hint**
1. **API Call:** `POST /hints/request_hint` with `user_id`, `problem_id`, `user_code`, `problem_data` (optional)
2. **Problem Lookup:** `_get_or_create_problem()` fetches or creates the problem.
3. **Progress Tracking:** `_get_user_progress()` fetches or creates a `UserProgress` for (user, problem).
4. **Attempts Count:** `attempts_count` is incremented.
5. **Time Tracking:** `time_since_last_attempt` is calculated. If >5min, `current_hint_level` is escalated.
6. **Hint History:** Last 5 delivered hints for (user, problem) are fetched.
7. **LLM Workflow:** `HintChain.process_hint_request()` is called with all context.
    - **Step 1:** Attempt is evaluated (LLM)
    - **Step 2:** Hint level/type updated
    - **Step 3:** New hint generated (LLM)
    - **Step 4:** Hint evaluated (LLM)
    - **Step 5:** If hint is duplicate of last, regenerate once
8. **Attempt Record:** Created with status (success/failed) and evaluation details.
9. **Failed Attempts:** `failed_attempts_count` incremented only if failed, reset to 0 on success.
10. **Hint, Evaluation, Delivery:** All records created and linked.
11. **Progress Saved:** All updates saved to DB.
12. **Response:** Hint, evaluation, and progress returned to user.

### **B. Auto-Trigger Workflow**
- Similar to above, but triggered if `UserProgress.is_stuck()` is True.
- Hint is auto-delivered and marked as such.

---

## 4. Function Reference

### **A. views.py: HintViewSet**

- **`request_hint(self, request)`**
  - Entry point for user hint requests.
  - Handles all progress, time, and hint history logic.
  - Calls `HintChain.process_hint_request()`.
  - Handles duplicate hint avoidance and failed attempt tracking.

- **`check_auto_trigger(self, request)`**
  - Checks if a hint should be auto-triggered for a stuck user.
  - Uses same workflow as `request_hint` but for auto-delivery.

- **`_get_or_create_problem(self, problem_id, problem_data)`**
  - Fetches or creates a `Problem`.

- **`_get_user_progress(self, user_id, problem)`**
  - Fetches or creates a `UserProgress` for (user, problem).

- **`_get_previous_hints(self, user_id, problem)`**
  - Returns last N delivered hints for (user, problem).

- **`_create_attempt(self, user_id, problem, user_code)`**
  - Evaluates the attempt and creates an `Attempt` record.

### **B. hint_chain.py: HintChain**

- **`__init__(self)`**
  - Initializes LLMs for each operation (attempt evaluation, hint generation, hint evaluation, auto-trigger).
  - Sets up LangSmith tracing if configured.

- **`_build_chains(self)`**
  - Constructs LangChain chains for each operation using custom prompts and output parsers.

- **`_build_main_workflow(self)`**
  - Orchestrates the main workflow: attempt evaluation → hint level/type update → hint generation → hint evaluation.

- **`process_hint_request(self, inputs)`**
  - Runs the main workflow chain with all user/problem context.
  - Returns attempt evaluation, generated hint, hint evaluation, and updated hint level/type.

- **`_get_next_hint_level(self, current_level, failed_attempts, time_since_last, attempt_evaluation)`**
  - Determines next hint level based on progress and LLM evaluation.

- **`_get_hint_type(self, hint_level, attempt_evaluation)`**
  - Maps hint level and evaluation to a hint type.

- **`_parse_attempt_evaluation(self, response)`**
  - Parses LLM output for attempt evaluation.

- **`_parse_hint_evaluation(self, response)`**
  - Parses LLM output for hint evaluation.

- **`_parse_auto_trigger_decision(self, response)`**
  - Parses LLM output for auto-trigger decision.

- **`evaluate_attempt_only(self, problem_description, user_code)`**
  - Standalone attempt evaluation (used in attempt creation).

### **C. prompts.py**
- **`get_hint_prompt(...)`**
  - Builds the prompt for hint generation, including user progress and previous hints.
- **`get_evaluation_prompt(...)`**
  - Builds the prompt for hint evaluation.
- **`get_auto_trigger_prompt(...)`**
  - Builds the prompt for auto-trigger decision.

### **D. langchain_service.py** (if used)
- **`generate_hint(...)`**
  - Generates a hint using LLM and conversation memory.
- **`evaluate_hint(...)`**
  - Evaluates a hint using LLM.
- **`evaluate_attempt(...)`**
  - Evaluates a user attempt using LLM.
- **`should_trigger_hint(...)`**
  - Decides if a hint should be auto-triggered.

---

## 5. Prompt Construction

Prompts are dynamically constructed to include:
- Problem description
- User code
- User progress (attempts, failures, hint level, time since last attempt)
- Previous hints (last 5)
- Current hint level/type

This ensures the LLM has full context for generating and evaluating hints.

---

## 6. End-to-End Example

1. **User submits code for Problem 42.**
2. **`request_hint`** is called with user_id=7, problem_id=42, user_code=...
3. **System fetches/creates Problem and UserProgress for (7, 42).**
4. **Attempts count incremented, time since last attempt calculated.**
5. **If inactive >5min, hint level escalated.**
6. **Last 5 hints for (7, 42) fetched.**
7. **`HintChain.process_hint_request`** is called:
    - LLM evaluates attempt (success/failure, reason, etc.)
    - Next hint level/type determined
    - LLM generates new hint
    - LLM evaluates hint
    - If hint is duplicate, regenerate once
8. **Attempt, Hint, HintEvaluation, HintDelivery records created.**
9. **Failed attempts incremented only if failed, reset on success.**
10. **User progress updated and saved.**
11. **Response returned: hint, evaluation, progress.**

---

## 7. Key Design Principles

- **Per-(user, problem) tracking:** All progress, attempts, and hint history are scoped to each user/problem pair.
- **Adaptive support:** System escalates help for stuck/inactive users.
- **No redundant hints:** Duplicate hints are avoided by checking recent history.
- **LLM-driven:** All evaluation, generation, and scoring is handled by LLMs with full context.
- **Observability:** LangSmith tracing and detailed logging at every step.
- **Robustness:** Safe data access, error handling, and fallback logic throughout.

---

# End-to-End Workflow: Detailed Step-by-Step

---

## 1. User Submits a Hint Request
- **API Endpoint:**  
  `POST /hints/request_hint`  
  (Handled by `HintViewSet.request_hint` in `views.py`)

---

## 2. Problem Lookup
- **Function:** `_get_or_create_problem(problem_id, problem_data)`
- **What Happens:**
  - Tries to fetch a `Problem` from the database using the provided `problem_id`.
  - **If found:** Returns the existing `Problem` object.
  - **If not found:**  
    - If `problem_data` is provided (with at least a title/description), creates a new `Problem` in the database.
    - If `problem_data` is missing, returns `None` and the request fails with a 404 error.
- **Code Reference:**
  ```python
  problem = self._get_or_create_problem(problem_id, problem_data)
  if not problem:
      return Response({'error': ...}, status=404)
  ```

---

## 3. User Progress Lookup/Creation
- **Function:** `_get_user_progress(user_id, problem)`
- **What Happens:**
  - Tries to fetch a `UserProgress` record for the (user, problem) pair.
  - **If found:** Returns the existing progress record.
  - **If not found:** Creates a new `UserProgress` with default values (`attempts_count=0`, `failed_attempts_count=0`, `current_hint_level=1`).
- **Code Reference:**
  ```python
  progress = self._get_user_progress(user_id, problem)
  ```

---

## 4. Update Attempts and Time Tracking
- **What Happens:**
  - Increments `progress.attempts_count` by 1.
  - Calculates `time_since_last_attempt` using the difference between now and `progress.last_activity`.
  - Updates `progress.last_activity` to now and saves the progress.
- **Special Logic:**  
  - If `time_since_last_attempt > 300` seconds (5 minutes), escalates `current_hint_level` by 1 (max 5).
- **Code Reference:**
  ```python
  progress.attempts_count += 1
  time_since_last_attempt = (timezone.now() - progress.last_activity).total_seconds() if progress.last_activity else 0
  progress.last_activity = timezone.now()
  if time_since_last_attempt > 300:
      progress.current_hint_level = min(progress.current_hint_level + 1, 5)
  progress.save()
  ```

---

## 5. Fetch Previous Hints (Hint History Context)
- **Function:** `_get_previous_hints(user_id, problem)`
- **What Happens:**
  - Fetches the last 5 `HintDelivery` records for this (user, problem), ordered by most recent.
  - Extracts the hint content for duplicate checking and LLM context.
- **Code Reference:**
  ```python
  previous_hints = list(self._get_previous_hints(user_id, problem)[:5])
  previous_hints_text = [hint.hint.content for hint in previous_hints]
  ```

---

## 6. Prepare LLM Workflow Input
- **What Happens:**
  - Gathers all relevant context: problem description, user code, attempts, failures, current hint level, time since last attempt, previous hints, etc.
  - Packs into a dictionary for the LLM workflow.
- **Code Reference:**
  ```python
  chain_input = {
      "problem_description": problem.description,
      "user_code": user_code,
      "attempts_count": progress.attempts_count,
      "failed_attempts_count": progress.failed_attempts_count,
      "current_hint_level": progress.current_hint_level,
      "time_since_last_attempt": time_since_last_attempt,
      "previous_hints": previous_hints_text,
      "hint_level": progress.current_hint_level,
      "hint_type": "conceptual"
  }
  ```

---

## 7. Run the Main LLM Workflow
- **Function:** `HintChain.process_hint_request(chain_input)`
- **What Happens:**
  - **Step 1:** LLM evaluates the attempt (success/failure, reason, etc.).
  - **Step 2:** System updates hint level/type based on evaluation.
  - **Step 3:** LLM generates a new hint using all context.
  - **Step 4:** LLM evaluates the generated hint (scores).
  - **Step 5:** If the new hint is a duplicate of the last delivered hint, the system regenerates once.
- **Code Reference:**
  ```python
  result = self.hint_chain.process_hint_request(chain_input)
  ```

---

## 8. Duplicate Hint Avoidance
- **What Happens:**
  - If the generated hint matches the most recent previous hint, the system regenerates once.
  - If still a duplicate, delivers as is (with a warning in logs).
- **Code Reference:**
  ```python
  if previous_hints_text and result['generated_hint'].strip() == previous_hints_text[0].strip():
      result = self.hint_chain.process_hint_request(chain_input)
  ```

---

## 9. Create Attempt Record
- **What Happens:**
  - Creates an `Attempt` record with the user's code, status (success/failed), and evaluation details.
- **Code Reference:**
  ```python
  attempt = Attempt.objects.create(
      user_id=user_id,
      problem=problem,
      code=user_code,
      status='failed' if not result['attempt_evaluation']['success'] else 'success',
      evaluation_details=result['attempt_evaluation']
  )
  ```

---

## 10. Update Failed Attempts Count
- **What Happens:**
  - If the attempt failed, increments `progress.failed_attempts_count`.
  - If the attempt succeeded, resets `progress.failed_attempts_count` to 0.
  - Saves progress.
- **Code Reference:**
  ```python
  if not result['attempt_evaluation']['success']:
      progress.failed_attempts_count += 1
  else:
      progress.failed_attempts_count = 0
  progress.save()
  ```

---

## 11. Create Hint, Evaluation, and Delivery Records
- **What Happens:**
  - Creates a `Hint` record with the generated content, level, and type.
  - Creates a `HintEvaluation` record with LLM scores.
  - Creates a `HintDelivery` record linking the hint, user, and attempt.
- **Code Reference:**
  ```python
  hint = Hint.objects.create(...)
  hint_evaluation = HintEvaluation.objects.create(...)
  hint_delivery = HintDelivery.objects.create(...)
  ```

---

## 12. Prepare and Return Response
- **What Happens:**
  - Packs the hint, evaluation, attempt ID, and user progress into a response dictionary.
  - Returns as the API response.
- **Code Reference:**
  ```python
  response_data = {...}
  return Response(response_data)
  ```

--- 