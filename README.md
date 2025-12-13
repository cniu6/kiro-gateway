<div align="center">

# 🚀 Kiro OpenAI Gateway

**OpenAI-compatible proxy gateway for Kiro IDE API (AWS CodeWhisperer)**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

*Use Claude models through any tools that support the OpenAI API*

[Features](#-features) • [Quick Start](#-quick-start) • [Configuration](#%EF%B8%8F-configuration) • [API Reference](#-api-reference) • [License](#-license)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔌 **OpenAI-compatible API** | Works with any OpenAI client out of the box |
| 💬 **Full message history** | Passes complete conversation context |
| 🛠️ **Tool Calling** | Supports function calling in OpenAI format |
| 📡 **Streaming** | Full SSE streaming support |
| 🔄 **Retry Logic** | Automatic retries on errors (403, 429, 5xx) |
| 📋 **Extended model list** | Including versioned models |
| 🔐 **Smart token management** | Automatic refresh before expiration |
| 🧩 **Modular architecture** | Easy to extend with new providers |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Kiro IDE refresh token ([how to get](#getting-the-refresh-token))

### Installation

```bash
# Clone the repository
git clone https://github.com/Jwadow/kiro-openai-gateway.git
cd kiro-openai-gateway

# Install dependencies
pip install -r requirements.txt

# Configure (see Configuration section)
cp .env.example .env
# Edit .env with your credentials

# Start the server
python main.py
```

The server will be available at `http://localhost:8000`

---

## ⚙️ Configuration

### Option 1: Environment Variables (.env file)

Create a `.env` file in the project root:

```env
# Required
REFRESH_TOKEN="your_kiro_refresh_token"

# Password to protect YOUR proxy server (make up any secure string)
# You'll use this as api_key when connecting to your gateway
PROXY_API_KEY="my-super-secret-password-123"

# Optional
PROFILE_ARN="arn:aws:codewhisperer:us-east-1:..."
KIRO_REGION="us-east-1"
```

### Option 2: JSON Credentials File

Specify the path to the credentials file:

```env
KIRO_CREDS_FILE="~/.aws/sso/cache/kiro-auth-token.json"

# Password to protect YOUR proxy server (make up any secure string)
PROXY_API_KEY="my-super-secret-password-123"
```

<details>
<summary>📄 JSON file format</summary>

```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "expiresAt": "2025-01-12T23:00:00.000Z",
  "profileArn": "arn:aws:codewhisperer:us-east-1:...",
  "region": "us-east-1"
}
```

</details>

### Getting the Refresh Token

The refresh token can be obtained by intercepting Kiro IDE traffic. Look for requests to:
- `prod.us-east-1.auth.desktop.kiro.dev/refreshToken`

---

## 📡 API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health check |
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completions |

### Available Models

| Model | Description |
|-------|-------------|
| `claude-opus-4-5` | Top-tier model |
| `claude-opus-4-5-20251101` | Top-tier model (versioned) |
| `claude-sonnet-4-5` | Enhanced model |
| `claude-sonnet-4-5-20250929` | Enhanced model (versioned) |
| `claude-sonnet-4` | Balanced model |
| `claude-sonnet-4-20250514` | Balanced model (versioned) |
| `claude-haiku-4-5` | Fast model |
| `claude-3-7-sonnet-20250219` | Legacy model |

---

## 💡 Usage Examples

<details>
<summary>🔹 Simple cURL Request</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

> **Note:** Replace `my-super-secret-password-123` with the `PROXY_API_KEY` you set in your `.env` file.

</details>

<details>
<summary>🔹 Streaming Request</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is 2+2?"}
    ],
    "stream": true
  }'
```

</details>

<details>
<summary>🔹 With Tool Calling</summary>

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer my-super-secret-password-123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "What is the weather in London?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "City name"}
          },
          "required": ["location"]
        }
      }
    }]
  }'
```

</details>

<details>
<summary>🐍 Python OpenAI SDK</summary>

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="my-super-secret-password-123"  # Your PROXY_API_KEY from .env
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

</details>

<details>
<summary>🦜 LangChain</summary>

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="my-super-secret-password-123",  # Your PROXY_API_KEY from .env
    model="claude-sonnet-4-5"
)

response = llm.invoke("Hello, how are you?")
print(response.content)
```

</details>

---

## 📁 Project Structure

```
kiro-openai-gateway/
├── main.py                    # Entry point, FastAPI app creation
├── requirements.txt           # Python dependencies
├── .env.example               # Environment configuration example
│
├── kiro_gateway/              # Main package
│   ├── __init__.py            # Package exports
│   ├── config.py              # Configuration and constants
│   ├── models.py              # Pydantic models for OpenAI API
│   ├── auth.py                # KiroAuthManager - token management
│   ├── cache.py               # ModelInfoCache - model caching
│   ├── utils.py               # Helper utilities
│   ├── converters.py          # OpenAI <-> Kiro conversion
│   ├── parsers.py             # AWS SSE stream parsers
│   ├── streaming.py           # Response streaming logic
│   ├── http_client.py         # HTTP client with retry logic
│   ├── debug_logger.py        # Debug logging (optional)
│   └── routes.py              # FastAPI routes
│
├── tests/                     # Tests
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
│
└── debug_logs/                # Debug logs (generated when enabled)
```

---

## 🔧 Debugging

Debug logging is **disabled by default**. To enable, add to your `.env`:

```env
DEBUG_LAST_REQUEST=true
```

When enabled, requests are logged to the `debug_logs/` folder:

| File | Description |
|------|-------------|
| `request_body.json` | Incoming request from client |
| `kiro_request_body.json` | Request to Kiro API |
| `response_stream_raw.txt` | Raw stream from Kiro |
| `response_stream_modified.txt` | Transformed stream |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest --cov=kiro_gateway
```

---

## 🔌 Extending with New Providers

The modular architecture makes it easy to add support for other providers:

1. Create a new module `kiro_gateway/providers/new_provider.py`
2. Implement the required classes:
   - `NewProviderAuthManager` — token management
   - `NewProviderConverter` — format conversion
   - `NewProviderParser` — response parsing
3. Add routes to `routes.py` or create a separate router

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:
- ✅ You can use, modify, and distribute this software
- ✅ You can use it for commercial purposes
- ⚠️ **You must disclose source code** when you distribute the software
- ⚠️ **Network use is distribution** — if you run a modified version on a server and let others interact with it, you must make the source code available to them
- ⚠️ Modifications must be released under the same license

See the [LICENSE](LICENSE) file for the full license text.

### Why AGPL-3.0?

AGPL-3.0 ensures that improvements to this software benefit the entire community. If you modify this gateway and deploy it as a service, you must share your improvements with your users.

### Contributor License Agreement (CLA)

By submitting a contribution to this project, you agree to the terms of our [Contributor License Agreement (CLA)](CLA.md). This ensures that:
- You have the right to submit the contribution
- You grant the maintainer rights to use and relicense your contribution
- The project remains legally protected

---

## 👤 Author

**Jwadow** — [@Jwadow](https://github.com/jwadow)

---

## ⚠️ Disclaimer

This project is not affiliated with, endorsed by, or sponsored by Amazon Web Services (AWS), Anthropic, or Kiro IDE. Use at your own risk and in compliance with the terms of service of the underlying APIs.

---

<div align="center">

**[⬆ Back to Top](#-kiro-openai-gateway)**

</div>
