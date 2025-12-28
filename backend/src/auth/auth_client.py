"""Authentication client for Streamlit app"""
import requests
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Backend API URL - must be set in environment variables
# Format: http://host:port (e.g., http://localhost:8000)
BACKEND_API_URL = os.getenv("BACKEND_API_URL")
if not BACKEND_API_URL:
    raise ValueError(
        "BACKEND_API_URL environment variable is required. "
        "Please set it in backend/.env file (e.g., BACKEND_API_URL=http://localhost:8000)"
    )


class AuthClient:
    """Client for interacting with the authentication backend"""
    
    def __init__(self, base_url: str = BACKEND_API_URL):
        self.base_url = base_url.rstrip('/')
        self.auth_base = f"{self.base_url}/api/auth"
    
    def signup(
        self, 
        email: str, 
        password: str, 
        full_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sign up a new user"""
        try:
            # Build request payload, only include non-None values
            payload = {
                "email": email,
                "password": password
            }
            if full_name:
                payload["full_name"] = full_name
            if username:
                payload["username"] = username
            
            response = requests.post(
                f"{self.auth_base}/signup",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = "Signup failed"
            if hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
            raise Exception(error_msg)
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and get tokens"""
        try:
            response = requests.post(
                f"{self.auth_base}/login",
                json={"email": email, "password": password},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = "Login failed"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
            raise Exception(error_msg)
    
    def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """Get current user information"""
        try:
            response = requests.get(
                f"{self.auth_base}/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = "Failed to get user info"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
            raise Exception(error_msg)
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            response = requests.post(
                f"{self.auth_base}/refresh",
                json={"refresh_token": refresh_token},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = "Token refresh failed"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
            raise Exception(error_msg)

