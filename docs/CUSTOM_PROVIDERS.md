# Custom Provider Registration Guide

PyTokenCalc supports **any LLM** you're running, including:

**Any Provider with API Endpoint:**
- RunPod serverless endpoints
- Llama Labs custom implementations  
- Replicate API
- Together AI
- HuggingFace Inference API
- Proprietary/private enterprise APIs

**Local Models (No Provider):**
- Custom trained models on your GPU/CPU
- Downloaded HuggingFace models running locally
- Fine-tuned models
- Proprietary models you've built
- Any open-source model you've downloaded and launched

**Bring Your Own Model (BYOM):**
- You run the inference server yourself
- PyTokenCalc queries YOUR server for token counts
- Works with any tokenization approach you use

## Quick Start

```python
from pytokencalc.tokenizers.custom_provider_counter import (
    CustomProviderCounter,
    register_custom_provider,
)
from pytokencalc.tokenizers import TokenCounterRegistry

# Create custom provider
counter = CustomProviderCounter(
    provider_name="my-provider",
    base_url="https://api.example.com",
    api_key="your-api-key"
)

# Register models
counter.register_models(["model-1", "model-2"])

# Register globally
register_custom_provider(counter)

# Use via registry
registry = TokenCounterRegistry()
result = registry.count_tokens("model-1", "Hello world", provider="my-provider")
print(f"Tokens: {result.input_tokens}")
```

## Examples by Provider

### RunPod Serverless

```python
from pytokencalc.tokenizers.custom_provider_counter import (
    CustomProviderCounter,
    register_custom_provider,
)

# RunPod endpoint (get your user_id from RunPod dashboard)
runpod = CustomProviderCounter(
    provider_name="runpod",
    base_url="https://api.runpod.io/v2/YOUR_USER_ID",
    api_key="your_runpod_api_key",
    api_path="/run"  # RunPod uses /run endpoint
)

# Register your deployed models
runpod.register_models([
    "llama-2-7b",
    "llama-2-13b",
    "mistral-7b",
])

register_custom_provider(runpod)

# Use it
from pytokencalc.tokenizers import TokenCounterRegistry
registry = TokenCounterRegistry()
result = registry.count_tokens("llama-2-7b", "Hello", provider="runpod")
```

### Llama Labs / LlamaIndex

```python
llama_labs = CustomProviderCounter(
    provider_name="llama-labs",
    base_url="https://api.llama-index.ai",  # or your custom endpoint
    api_key="your_llama_labs_key"
)

llama_labs.register_models([
    "llama-index-7b",
    "llama-index-13b",
    "llama-index-chat",
])

register_custom_provider(llama_labs)
```

### Replicate API

```python
replicate = CustomProviderCounter(
    provider_name="replicate",
    base_url="https://api.replicate.com/v1",
    api_key="your_replicate_token"
)

# Register Replicate models
replicate.register_models([
    "meta/llama-2-7b",
    "mistralai/mistral-7b",
    "replicate/year-2024-model",
])

register_custom_provider(replicate)
```

### Together AI

```python
together = CustomProviderCounter(
    provider_name="together-ai",
    base_url="https://api.together.xyz",
    api_key="your_together_api_key"
)

together.register_models([
    "meta-llama/Llama-2-7b-hf",
    "meta-llama/Llama-2-13b-hf",
    "mistralai/Mistral-7B-Instruct-v0.1",
])

register_custom_provider(together)
```

### HuggingFace Inference API

```python
hf_inference = CustomProviderCounter(
    provider_name="huggingface",
    base_url="https://api-inference.huggingface.co/v1",
    api_key="your_hf_token"
)

hf_inference.register_models([
    "meta-llama/Llama-2-7b",
    "mistralai/Mistral-7B-Instruct-v0.1",
    "gpt2",
])

register_custom_provider(hf_inference)
```

### Docker Container Deployment

```bash
# Run LLM in Docker
docker run -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm:latest \
  --model meta-llama/Llama-2-7b-hf
```

```python
# Register Docker-based LLM with PyTokenCalc
docker_llm = CustomProviderCounter(
    provider_name="docker-llama",
    base_url="http://localhost:8000",
    api_key=None
)

docker_llm.register_models(["meta-llama/Llama-2-7b-hf"])
register_custom_provider(docker_llm)

# Use it
registry.count_tokens("meta-llama/Llama-2-7b-hf", text, provider="docker-llama")
```

### Kubernetes Deployment

```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm
  template:
    metadata:
      labels:
        app: llm
    spec:
      containers:
      - name: vllm
        image: vllm/vllm:latest
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_NAME
          value: "meta-llama/Llama-2-7b-hf"
---
apiVersion: v1
kind: Service
metadata:
  name: llm-service
spec:
  selector:
    app: llm
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

```python
# Register Kubernetes-based LLM
k8s_llm = CustomProviderCounter(
    provider_name="k8s-llama",
    base_url="http://llm-service.default:8000",  # K8s service DNS
    api_key=None
)

k8s_llm.register_models(["meta-llama/Llama-2-7b-hf"])
register_custom_provider(k8s_llm)

# Use it (now using Kubernetes pod)
registry.count_tokens("meta-llama/Llama-2-7b-hf", text, provider="k8s-llama")
```

### Docker Compose Multi-Container

```yaml
# docker-compose.yml
version: '3.8'
services:
  llm-inference:
    image: vllm/vllm:latest
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=meta-llama/Llama-2-7b-hf
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    
  app:
    image: my-app:latest
    ports:
      - "5000:5000"
    depends_on:
      - llm-inference
    environment:
      - LLM_URL=http://llm-inference:8000
```

```python
# Register Docker Compose LLM
compose_llm = CustomProviderCounter(
    provider_name="compose-llama",
    base_url="http://llm-inference:8000",  # Service name from Docker Compose
    api_key=None
)

compose_llm.register_models(["meta-llama/Llama-2-7b-hf"])
register_custom_provider(compose_llm)
```

### Custom Self-Hosted Solution

```python
# Your custom self-hosted model server
custom = CustomProviderCounter(
    provider_name="internal-server",
    base_url="http://internal-ml.company.com:8080",
    api_key=None  # No auth required for internal
)

custom.register_models([
    "company-llm-v1",
    "company-llm-v2",
])

register_custom_provider(custom)
```

### Bring Your Own Model (BYOM)

User downloads and runs a model locally on their GPU/CPU, then exposes it via an API.

**Example: User's Custom Setup**
```
1. Download Llama-2 from HuggingFace
   $ huggingface-cli download meta-llama/Llama-2-7b-hf

2. Run inference server
   $ python -m vllm.entrypoints.openai_api_server \
       --model meta-llama/Llama-2-7b-hf \
       --port 8000

3. Register with PyTokenCalc
```

```python
from pytokencalc.tokenizers.custom_provider_counter import (
    CustomProviderCounter,
    register_custom_provider,
)

# User's locally-running model
my_model = CustomProviderCounter(
    provider_name="my-local-llm",
    base_url="http://localhost:8000",  # Your inference server
    api_key=None,
)

# Register the model you're running
my_model.register_models(["meta-llama/Llama-2-7b-hf"])

register_custom_provider(my_model)

# Now use it in your application
from pytokencalc.tokenizers import TokenCounterRegistry
registry = TokenCounterRegistry()
result = registry.count_tokens("meta-llama/Llama-2-7b-hf", text, provider="my-local-llm")
```

**User's Inference Framework Options:**
- **vLLM**: Fast inference engine for HuggingFace models
- **llama.cpp**: C++ inference for Llama models (very fast)
- **GPTQ**: Quantized inference
- **DeepSpeed**: Microsoft's inference optimization
- **Text Generation WebUI**: Gradio-based web interface
- **SpeakLeash**: Local LLM control panel
- **Ray Serve**: Scalable model serving
- **FastAPI + Transformers**: Custom wrapper around HF models

**Deployment Options:**
- **Docker Container**: Run LLM in isolated Docker container
- **Kubernetes Pod**: Run LLM in Kubernetes cluster
- **Docker Compose**: Multi-container orchestration
- **Local GPU/CPU**: Direct inference on user's machine

**Example: User runs fine-tuned model**
```python
# User trained their own model
my_finetuned = CustomProviderCounter(
    provider_name="my-finetuned-model",
    base_url="http://localhost:9000",
    verify_provider=False  # Skip verification, might not be running yet
)

my_finetuned.register_models(["my-company-chat-v1", "my-company-chat-v2"])
register_custom_provider(my_finetuned)

# Use in PyTokenCalc
result = registry.count_tokens("my-company-chat-v1", text, provider="my-finetuned-model")
```

**Example: User's proprietary model (no external provider)**
```python
# User has a proprietary model they've built
proprietary = CustomProviderCounter(
    provider_name="proprietary-model",
    base_url="http://internal-server:5000",
    api_key="internal-auth-token",
)

proprietary.register_models(["proprietary-v1", "proprietary-v2"])
register_custom_provider(proprietary)

# PyTokenCalc works with it seamlessly
result = registry.count_tokens("proprietary-v1", text, provider="proprietary-model")
```

**Key Point**: It doesn't matter if the model is trained by OpenAI, Google, Meta, or by the user themselves. PyTokenCalc supports ANY LLM as long as:
1. There's an API endpoint (even if it's just on localhost)
2. User registers the model name
3. Custom token extraction logic is provided if needed

**No provider lock-in. No limitations. Any LLM works.**

## Custom Token Extraction

If your provider uses a non-standard response format:

```python
def extract_tokens_from_custom_format(response):
    """Extract tokens from provider's response format"""
    # Your provider might return: {"result": {"tokens_processed": 100}}
    return response["result"]["tokens_processed"]

custom = CustomProviderCounter(
    provider_name="my-provider",
    base_url="https://api.example.com",
    api_key="key",
    token_extraction_fn=extract_tokens_from_custom_format
)

custom.register_models(["my-model"])
register_custom_provider(custom)
```

## Supported Response Formats

CustomProviderCounter automatically handles these response formats:

### 1. OpenAI-Compatible (Default)
```json
{
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50
  }
}
```

### 2. Simple Token Count
```json
{
  "tokens": 100
}
```

### 3. Alternative Format
```json
{
  "token_count": 100
}
```

### 4. Prompt Tokens Only
```json
{
  "prompt_tokens": 100
}
```

## Platform Awareness

⚠️ **IMPORTANT**: Same model on different platforms may have DIFFERENT token counts

```python
# Register same model on multiple platforms
runpod = CustomProviderCounter(...)
runpod.register_models(["llama-2-7b"])
register_custom_provider(runpod)

together = CustomProviderCounter(...)
together.register_models(["llama-2-7b"])
register_custom_provider(together)

# These will return different token counts
registry = TokenCounterRegistry()
result1 = registry.count_tokens("llama-2-7b", text, provider="runpod")
result2 = registry.count_tokens("llama-2-7b", text, provider="together-ai")

# ✓ CORRECT: Keep results separate by platform
print(f"RunPod: {result1.input_tokens} tokens (platform: {result1.platform})")
print(f"Together: {result2.input_tokens} tokens (platform: {result2.platform})")

# ✗ WRONG: Do NOT aggregate
# avg = (result1.input_tokens + result2.input_tokens) / 2  # BAD!
```

## Verification & Debugging

### Check if Provider is Registered

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()
providers = registry.list_providers()
print(f"Available providers: {providers}")

# Check specific provider
counter = registry.get_counter("my-provider")
if counter:
    print(f"Models: {counter.supported_models}")
else:
    print("Provider not found")
```

### Test Provider Connection

```python
counter = CustomProviderCounter(
    provider_name="test",
    base_url="https://api.example.com",
    api_key="key",
    verify_provider=True  # This will test connectivity
)
```

### Manual Token Counting

```python
counter = registry.get_counter("my-provider")
text = "Hello world"
result = counter.count(text, "my-model")
print(f"Tokens: {result.input_tokens}")
print(f"Latency: {result.latency_ms}ms")
print(f"Platform: {result.platform}")
```

## Common Issues

### Issue: "Model not found" Error

**Problem**: Provider returns 404 for model
```
ValueError: Model 'llama-2-7b' not recognized for provider 'my-provider'.
Available: []. Register with: counter.register_model('llama-2-7b')
```

**Solution**: Models must be explicitly registered
```python
counter.register_model("llama-2-7b")
# or
counter.register_models(["llama-2-7b", "mistral-7b"])
```

### Issue: "API error" or Connection Refused

**Problem**: Can't connect to provider
```
RuntimeError: Failed to count tokens with my-provider: Connection refused
```

**Solution**: Verify:
1. Provider is running/accessible: `curl https://api.example.com/models`
2. Correct base URL and API key
3. Firewall/proxy not blocking
4. API key has correct permissions

### Issue: "Unexpected JSON" Error

**Problem**: Provider returns non-JSON response
```
requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1
```

**Solution**: Provide custom token extraction:
```python
def extract_tokens(response):
    # Verify response format
    print(f"Response: {response}")
    return response.get("your_token_field", 0)

counter = CustomProviderCounter(
    provider_name="my-provider",
    base_url="...",
    api_key="...",
    token_extraction_fn=extract_tokens
)
```

## Best Practices

1. **Always Register Models Explicitly**
   ```python
   counter.register_models(["model-1", "model-2"])
   ```

2. **Use Clear Provider Names**
   ```python
   register_custom_provider(runpod)  # vs "rp" or "r"
   ```

3. **Keep Platform Results Separate**
   ```python
   # Store with platform info
   result_runpod = registry.count_tokens(..., provider="runpod")
   result_together = registry.count_tokens(..., provider="together-ai")
   # Keep separate, don't mix
   ```

4. **Test Token Extraction**
   ```python
   # Verify extraction works
   response = provider_api_call()
   tokens = counter.token_extraction_fn(response)
   assert tokens > 0
   ```

5. **Cache Results**
   ```python
   from pytokencalc.tokenizers import TokenCounterRegistry
   registry = TokenCounterRegistry()
   # Repeated calls for same text/model are cached
   ```

## Advanced: Custom Extraction with Error Handling

```python
def smart_token_extraction(response):
    """Extract tokens with multiple fallbacks"""
    # Try OpenAI format
    if "usage" in response and "prompt_tokens" in response["usage"]:
        return response["usage"]["prompt_tokens"]
    
    # Try direct format
    for key in ["tokens", "token_count", "prompt_tokens", "num_tokens"]:
        if key in response:
            return response[key]
    
    # Try nested formats
    if "data" in response and isinstance(response["data"], dict):
        return response["data"].get("tokens", 0)
    
    # Fallback: estimate from response
    return len(str(response)) // 4

counter = CustomProviderCounter(
    provider_name="flexible",
    base_url="...",
    token_extraction_fn=smart_token_extraction
)
```

## Environment Variables for API Keys

Recommended: Use environment variables, don't hardcode keys

```python
import os
from pytokencalc.tokenizers.custom_provider_counter import CustomProviderCounter

api_key = os.getenv("RUNPOD_API_KEY")
if not api_key:
    raise ValueError("Set RUNPOD_API_KEY environment variable")

runpod = CustomProviderCounter(
    provider_name="runpod",
    base_url="https://api.runpod.io/v2/xxx",
    api_key=api_key
)
```

## Support

For issues with specific providers:

1. Check provider documentation for:
   - Correct API endpoint
   - Authentication requirements
   - Response format
   - Rate limiting

2. Test with curl first:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" \
        https://api.example.com/v1/completions \
        -d '{"model": "model-name", "prompt": "test"}'
   ```

3. Create custom extraction function to match provider format

4. Open issue with provider details (sanitized)
