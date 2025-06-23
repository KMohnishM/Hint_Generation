# LangSmith Setup Guide

## 🚀 Quick Setup

### 1. Get LangSmith API Key
1. Go to [LangSmith](https://smith.langchain.com/)
2. Sign up/Login with your account
3. Navigate to **Settings** → **API Keys**
4. Click **Create API Key**
5. Copy the API key

### 2. Configure Environment Variables
Create a `.env` file in the `backend/` directory with:

```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=hint-generation-system
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_V2=true

# Django Configuration
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

### 3. Restart Your Server
```bash
# Stop the current server (Ctrl+C)
# Then restart
python manage.py runserver
```

## 📊 What You'll See in LangSmith

### **Dashboard Overview:**
- **Traces**: Every LLM call with prompts and responses
- **Chains**: Visual representation of your workflows
- **Performance**: Latency and cost metrics
- **Projects**: Organized by your project name

### **Key Sections:**

#### **1. Traces Tab**
- Every hint generation request
- Every code evaluation
- Every auto-trigger decision
- Full prompts and responses
- Timing information

#### **2. Projects Tab**
- Your project: `hint-generation-system`
- All traces organized by project
- Performance analytics

#### **3. Datasets Tab**
- Create test datasets
- A/B test different prompts
- Compare hint quality

#### **4. Prompts Tab**
- All prompts used in your system
- Version history
- Performance metrics

## 🔍 How to Navigate

### **View Recent Traces:**
1. Go to [LangSmith Dashboard](https://smith.langchain.com/)
2. Click on your project: `hint-generation-system`
3. You'll see recent traces listed
4. Click on any trace to see details

### **Trace Details Include:**
- **Input**: The prompt sent to the LLM
- **Output**: The response received
- **Timing**: How long the request took
- **Cost**: API usage cost
- **Metadata**: Additional context

### **Filter and Search:**
- Filter by date range
- Search by trace name
- Filter by status (success/error)
- Sort by performance metrics

## 🧪 Test Your Integration

### **Make Some API Calls:**
```bash
# Test hint request
curl -X POST http://127.0.0.1:8000/api/hints/request_hint/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "problem_id": 1,
    "user_code": "def twoSum(nums, target):\n    pass",
    "problem_data": {
      "title": "Two Sum",
      "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target."
    }
  }'
```

### **Check LangSmith Dashboard:**
1. Wait 30-60 seconds for traces to appear
2. Refresh your LangSmith dashboard
3. You should see new traces appear

## 📈 What to Look For

### **Successful Integration:**
- ✅ Traces appearing in real-time
- ✅ Full prompts and responses visible
- ✅ Performance metrics showing
- ✅ No error messages in traces

### **Common Issues:**
- ❌ No traces appearing: Check API key
- ❌ Traces with errors: Check OpenRouter API key
- ❌ Empty responses: Check model availability

## 🎯 Next Steps

### **1. Monitor Performance:**
- Track response times
- Monitor API costs
- Identify slow operations

### **2. Optimize Prompts:**
- A/B test different prompt strategies
- Compare hint quality scores
- Iterate on prompt design

### **3. Debug Issues:**
- Use traces to debug failed requests
- Analyze error patterns
- Optimize error handling

### **4. Scale Up:**
- Create datasets for testing
- Set up automated evaluations
- Monitor system health

## 🔧 Troubleshooting

### **No Traces Appearing:**
1. Check if `LANGSMITH_API_KEY` is set correctly
2. Verify `LANGSMITH_TRACING_V2=true`
3. Restart your Django server
4. Wait 1-2 minutes for traces to appear

### **API Key Issues:**
1. Ensure the API key is valid
2. Check if you have the correct permissions
3. Verify the project name matches

### **Performance Issues:**
1. Check response times in traces
2. Monitor API rate limits
3. Optimize prompt length

## 📞 Support

If you're still not seeing traces:
1. Check the Django logs for LangSmith errors
2. Verify your API key is working
3. Try making a simple test call
4. Contact LangSmith support if needed

---

**Happy Monitoring! 🚀** 