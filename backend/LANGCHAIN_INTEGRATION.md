# LangChain & LangSmith Integration Guide

This document explains how to integrate LangChain and LangSmith into your hint generation system.

## 🚀 Benefits

### LangChain Benefits:
- **Structured Prompts**: Better prompt management and templating
- **Memory Systems**: Track conversation history and user context
- **Chains & Agents**: More sophisticated reasoning workflows
- **Output Parsing**: Structured responses from LLM
- **Tool Integration**: Easy integration with external APIs
- **Caching**: Improve performance and reduce API costs

### LangSmith Benefits:
- **Observability**: Track all LLM calls, prompts, and responses
- **Debugging**: Visualize chains and debug issues
- **Performance Monitoring**: Track latency, costs, and success rates
- **A/B Testing**: Compare different prompt strategies
- **Dataset Management**: Create and test with datasets
- **Collaboration**: Team can share and iterate on prompts

## 📦 Installation

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up Environment Variables**:
Create a `.env` file in the `backend/` directory:

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

## 🔧 Configuration

### 1. LangSmith Setup

1. **Get LangSmith API Key**:
   - Go to [LangSmith](https://smith.langchain.com/)
   - Sign up and create an account
   - Navigate to API Keys section
   - Create a new API key

2. **Configure Environment**:
   - Set `LANGSMITH_API_KEY` in your `.env` file
   - Set `LANGSMITH_PROJECT` to your project name
   - Enable tracing with `LANGSMITH_TRACING_V2=true`

### 2. LangChain Service

The new `LangChainService` replaces the old `OpenRouterService` with:

- **Structured Output Parsing**: Using Pydantic models
- **Conversation Memory**: Track user interactions
- **Prompt Templates**: Better prompt management
- **Chain Composition**: Modular LLM workflows

## 🏗️ Architecture

### New Components:

1. **LangChainService** (`hints/langchain_service.py`):
   - Handles all LLM interactions
   - Manages conversation memory
   - Provides structured output parsing
   - Integrates with LangSmith for observability

2. **Pydantic Models**:
   - `AttemptEvaluation`: Structured code evaluation
   - `HintEvaluation`: Quality assessment scores
   - `AutoTriggerDecision`: Auto-trigger logic

3. **Prompt Templates**:
   - Structured, reusable prompts
   - Better context management
   - Easier to iterate and improve

## 🔄 Migration from Old Service

### Changes Made:

1. **Service Import**:
   ```python
   # Old
   from .services import OpenRouterService
   
   # New
   from .langchain_service import LangChainService
   ```

2. **Service Initialization**:
   ```python
   # Old
   self.openrouter_service = OpenRouterService()
   
   # New
   self.langchain_service = LangChainService()
   ```

3. **Method Calls**:
   - All method calls remain the same
   - Return formats are identical
   - No changes needed in views or other components

## 📊 LangSmith Dashboard

### What You'll See:

1. **Traces**: Every LLM call is tracked
2. **Chains**: Visual representation of your workflows
3. **Prompts**: All prompts and responses
4. **Performance**: Latency and cost metrics
5. **Feedback**: User feedback and evaluations

### Key Metrics:

- **Latency**: Response times for each operation
- **Cost**: API usage and costs
- **Success Rate**: Successful vs failed operations
- **User Satisfaction**: Hint quality scores

## 🧪 Testing

### 1. Test LangChain Service:

```python
from hints.langchain_service import LangChainService

service = LangChainService()

# Test hint generation
hint = service.generate_hint(
    problem_description="Two Sum problem",
    user_code="def twoSum(nums, target): pass",
    previous_hints=[],
    hint_level=1,
    user_progress={"attempts_count": 1, "failed_attempts_count": 0},
    hint_type="conceptual"
)

print(hint)
```

### 2. Test LangSmith Integration:

1. Make a few API calls
2. Check your LangSmith dashboard
3. Verify traces are being created
4. Review prompt and response data

## 🔍 Debugging

### Common Issues:

1. **LangSmith Not Showing Data**:
   - Check API key is correct
   - Verify environment variables are set
   - Ensure tracing is enabled

2. **Import Errors**:
   - Install all dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility

3. **Memory Issues**:
   - Memory is per-service instance
   - Consider implementing per-user memory storage

## 🚀 Advanced Features

### 1. Custom Chains:

```python
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate

# Create custom chain
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("human", "{input}")
])

chain = LLMChain(llm=service.llm, prompt=prompt)
result = chain.run(input="Hello!")
```

### 2. Memory Management:

```python
# Clear memory for specific user
service.clear_memory(user_id=123, problem_id=1)

# Access memory
messages = service.memory.chat_memory.messages
```

### 3. Custom Output Parsers:

```python
from pydantic import BaseModel, Field

class CustomOutput(BaseModel):
    result: str = Field(description="The result")
    confidence: float = Field(description="Confidence score")

parser = PydanticOutputParser(pydantic_object=CustomOutput)
```

## 📈 Performance Optimization

### 1. Caching:

```python
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

# Enable caching
set_llm_cache(InMemoryCache())
```

### 2. Batch Processing:

```python
# Process multiple requests together
results = service.llm.batch([
    "Request 1",
    "Request 2",
    "Request 3"
])
```

### 3. Streaming:

```python
# Stream responses
for chunk in service.llm.stream("Your prompt"):
    print(chunk.content, end="")
```

## 🔐 Security Considerations

1. **API Key Management**:
   - Never commit API keys to version control
   - Use environment variables
   - Rotate keys regularly

2. **Input Validation**:
   - Validate all user inputs
   - Sanitize code before sending to LLM
   - Implement rate limiting

3. **Output Filtering**:
   - Filter inappropriate content
   - Validate structured outputs
   - Handle parsing errors gracefully

## 📚 Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🤝 Contributing

When contributing to the LangChain integration:

1. **Follow LangChain Best Practices**:
   - Use structured outputs
   - Implement proper error handling
   - Add comprehensive logging

2. **Test Thoroughly**:
   - Test with different inputs
   - Verify LangSmith traces
   - Check performance impact

3. **Document Changes**:
   - Update this guide
   - Add inline comments
   - Update API documentation 