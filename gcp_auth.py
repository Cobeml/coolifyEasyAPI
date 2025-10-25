import os
import json
import time
import base64
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def base64url_encode(data: bytes) -> str:
    """Base64url encoding helper function."""
    return base64.b64encode(data).decode('utf-8').rstrip('=').replace('+', '-').replace('/', '_')


def create_jwt_token() -> str:
    """
    Create a signed JWT token for Google Cloud Platform authentication.
    
    Required environment variables:
    - GCP_PRIVATE_KEY: The private key from the service account JSON
    - GCP_KEY_ID: The key ID from the service account JSON  
    - GCP_CLIENT_EMAIL: The client email from the service account JSON
    
    Returns:
        str: The signed JWT token
    """
    # Get required environment variables
    private_key_str = os.getenv('GCP_PRIVATE_KEY')
    key_id = os.getenv('GCP_KEY_ID')
    client_email = os.getenv('GCP_CLIENT_EMAIL')
    
    if not all([private_key_str, key_id, client_email]):
        raise ValueError("Missing required environment variables: GCP_PRIVATE_KEY, GCP_KEY_ID, GCP_CLIENT_EMAIL")
    
    # Replace escaped newlines in private key
    private_key_str = private_key_str.replace('\\n', '\n')
    
    # Load the private key
    private_key = serialization.load_pem_private_key(
        private_key_str.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    
    # Create timestamps
    iat = int(time.time())
    exp = iat + 3600  # 1 hour expiry
    
    # JWT header with kid
    header = {
        "alg": "RS256",
        "typ": "JWT",
        "kid": key_id
    }
    
    # JWT payload claims
    payload = {
        "iss": client_email,
        "sub": client_email,
        "aud": "https://oauth2.googleapis.com/token",
        "iat": iat,
        "exp": exp,
        "scope": "https://www.googleapis.com/auth/generative-language https://www.googleapis.com/auth/cloud-platform"
    }
    
    # Encode header and payload
    encoded_header = base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    encoded_payload = base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    # Create data to sign
    data_to_sign = f"{encoded_header}.{encoded_payload}"
    
    # Sign the data
    signature = private_key.sign(
        data_to_sign.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    # Encode signature
    encoded_signature = base64url_encode(signature)
    
    # Create final JWT
    jwt_token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
    
    return jwt_token


def get_oauth_access_token() -> str:
    """
    Exchange JWT for OAuth2 access token.
    
    Returns:
        str: OAuth2 access token that can be used for API calls
        
    Raises:
        requests.exceptions.RequestException: For network/HTTP errors
        ValueError: For authentication errors
    """
    # Create the JWT assertion
    jwt_token = create_jwt_token()
    
    # Exchange JWT for access token
    token_url = "https://oauth2.googleapis.com/token"
    
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(token_url, data=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise ValueError(f"No access token in response: {token_data}")
            
        return access_token
        
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to get access token: {str(e)}") from e
    except (ValueError, KeyError) as e:
        try:
            error_info = response.json()
            raise ValueError(f"Token exchange failed: {error_info}") from e
        except:
            raise ValueError(f"Token exchange failed: {response.text}") from e


def authenticate_gcp() -> str:
    """
    Main function to authenticate with GCP and return an access token.
    
    This function handles the complete authentication flow:
    1. Creates a JWT token using service account credentials
    2. Exchanges the JWT for an OAuth2 access token
    3. Returns the access token for use with GCP APIs
    
    Returns:
        str: OAuth2 access token that can be used for GCP API calls
        
    Raises:
        ValueError: If authentication fails or credentials are missing
        requests.exceptions.RequestException: If network/HTTP errors occur
    """
    print("[AUTH] Starting GCP authentication process...")
    
    try:
        # Get the OAuth2 access token
        access_token = get_oauth_access_token()
        print("[AUTH] Successfully obtained GCP access token")
        
        return access_token
        
    except Exception as e:
        print(f"[AUTH] Authentication failed: {str(e)}")
        raise
