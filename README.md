# coolifyEasyAPI

A FastAPI starter template with Bearer token authentication for quick deployment in Coolify.

## Features

- 🔐 **Bearer Token Authentication** - Secure API access
- 🚀 **FastAPI** - Modern, fast web framework
- 📦 **Ready to Deploy** - Optimized for Coolify deployment
- 🐍 **Python 3.8+** - Built with modern Python

## Quick Start

### 1. Set Environment Variable
```bash
export BEARER_KEY="your_secret_key_here"
```

### 2. Test the API

**Root endpoint:**
```bash
curl -H "Authorization: Bearer your_secret_key_here" http://localhost:8000/
```

**Items endpoint:**
```bash
curl -H "Authorization: Bearer your_secret_key_here" http://localhost:8000/items/123
```

**With query parameter:**
```bash
curl -H "Authorization: Bearer your_secret_key_here" "http://localhost:8000/items/123?q=test"
```

## Deployment

This template is designed for quick deployment in Coolify. For detailed setup instructions, see the [Coolify FastAPI UV Tutorial](https://blog.rayberger.org/coolify-fastapi-uv).

## Security Note

⚠️ **For development/testing only** - This basic Bearer token implementation lacks rate limiting and other production security features.