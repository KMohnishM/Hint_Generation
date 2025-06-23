# LangSmith Troubleshooting Guide

## Issue: Can't See Traces in LangSmith Dashboard

### ✅ What's Working:
- LANGCHAIN_API_KEY is set correctly
- LangChainService initializes successfully
- LLM is available and working

### ❌ The Problem:
**Tracing is disabled!** The environment variable `LANGSMITH_TRACING_V2` is not set to `true`.

## 🔧 How to Fix:

### Step 1: Set Environment Variables

You need to set these environment variables. You can do this in several ways:

#### Option A: Create a .env file (Recommended)
Create a file called `.env` in the `backend` directory:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# LangSmith Configuration
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=hg
LANGSMITH_TRACING_V2=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

#### Option B: Set Environment Variables Directly
```bash
# Windows PowerShell
$env:LANGCHAIN_API_KEY="your_langsmith_api_key_here"
$env:LANGSMITH_PROJECT="hg"
$env:LANGSMITH_TRACING_V2="true"
$env:LANGSMITH_ENDPOINT="https://api.smith.langchain.com"

# Linux/Mac
export LANGCHAIN_API_KEY="your_langsmith_api_key_here"
export LANGSMITH_PROJECT="hg"
export LANGSMITH_TRACING_V2="true"
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
```

### Step 2: Get Your LangSmith API Key

1. Go to [https://smith.langchain.com/settings](https://smith.langchain.com/settings)
2. Click on "API Keys" in the left sidebar
3. Create a new API key or copy an existing one
4. Use this key as your `LANGCHAIN_API_KEY`

### Step 3: Verify Configuration

Run the test script again:
```bash
cd backend
python test_langsmith_config.py
```

You should see:
```
LANGSMITH_TRACING_V2: true
Tracing enabled: ✅ Yes
```

### Step 4: Test with Real Request

Make a request to your hint system and then check:
1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Look for the project "hg"
3. You should see traces appearing in real-time

## 🔍 What to Look For in LangSmith:

### Traces Should Show:
- **Input**: The problem description and user code
- **Output**: The generated hint
- **Metadata**: Hint level, type, evaluation scores
- **Timing**: How long each step took

### Expected Trace Structure:
```
Hint Generation Request
├── Problem Analysis
├── Hint Generation
├── Hint Evaluation
└── Response Preparation
```

## 🚨 Common Issues:

### 1. "No traces found"
- Check that `LANGSMITH_TRACING_V2=true`
- Verify your API key is correct
- Make sure you're looking at the right project

### 2. "Invalid API key"
- Get a fresh API key from LangSmith settings
- Make sure you're using `LANGCHAIN_API_KEY` (not `LANGSMITH_API_KEY`)

### 3. "Project not found"
- The project will be created automatically when first trace is sent
- Make sure `LANGSMITH_PROJECT=hg`

### 4. "Traces not updating"
- LangSmith has a slight delay (usually 10-30 seconds)
- Try refreshing the page
- Check that your Django server is running

## 🎯 Quick Test:

After setting the environment variables, make a request to your hint API:

```bash
curl -X POST http://localhost:8000/api/hints/request_hint/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "problem_id": 1,
    "user_code": "def test(): pass",
    "problem_data": {
      "title": "Test Problem",
      "description": "This is a test problem"
    }
  }'
```

Then immediately check your LangSmith dashboard - you should see the trace appear within 30 seconds.

## 📊 Expected Results:

Once working, you should see in LangSmith:
- ✅ Real-time traces for each hint request
- ✅ Detailed input/output for each LLM call
- ✅ Performance metrics and timing
- ✅ Error tracking if something goes wrong
- ✅ Conversation history and context

## 🆘 Still Not Working?

If you're still not seeing traces:

1. **Check the logs**: Look for any LangSmith-related errors in your Django logs
2. **Verify network**: Make sure your server can reach `https://api.smith.langchain.com`
3. **Test API key**: Try the API key in a simple LangChain script
4. **Check permissions**: Make sure your LangSmith account has API access

Let me know what you see in the test script after setting the environment variables! 