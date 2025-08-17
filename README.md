# coolifyEasyAPI

A FastAPI starter template with Bearer token authentication for quick deployment in Coolify.

## Quick Setup

1. **Clone or fork this repository**
2. **Create a Coolify resource** that pulls from your public GitHub repo
3. **Coolify will automatically detect** the nixpacks build type
4. **Set your BEARER_KEY** as an environment variable in the Coolify resource settings
5. **Save and redeploy** the resource

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
curl -H "Authorization: Bearer $BEARER_KEY" http://localhost:8000/
```

**Items endpoint:**
```bash
curl -H "Authorization: Bearer $BEARER_KEY" http://localhost:8000/items/123
```

**With query parameter:**
```bash
curl -H "Authorization: Bearer $BEARER_KEY" "http://localhost:8000/items/123?q=test"
```

## Security Note

⚠️ **For development/testing only** - This basic Bearer token implementation lacks rate limiting and other production security features.

## Further Instructions

For detailed setup instructions in Coolify, see the [Coolify FastAPI UV Tutorial](https://blog.rayberger.org/coolify-fastapi-uv).