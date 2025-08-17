import os
from typing import Union
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

# Get the bearer key from environment variable
BEARER_KEY = os.getenv("BEARER_KEY")

# Security scheme for receiving the bearer token
security = HTTPBearer()

# Dependency to enforce Bearer token auth
def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme."
        )
    token = credentials.credentials
    if token != BEARER_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token."
        )
    # Authorized
    return token

@app.get("/")
def read_root(token: str = Depends(verify_bearer_token)):
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None, token: str = Depends(verify_bearer_token)):
    return {"item_id": item_id, "q": q}
