"""Pydantic schemas for API responses"""
from typing import Any, Optional
from pydantic import BaseModel, Field

class StandardResponse(BaseModel):
    """Standardized API response format"""
    status_code: int = Field(..., description="HTTP status code", example=200)
    status: bool = Field(..., description="Operation status (true/false)", example=True)
    message: str = Field(..., description="Response message", example="Success")
    path: str = Field(..., description="API endpoint path", example="/api/endpoint")
    data: Optional[Any] = Field(None, description="Response data")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status_code": 200,
                    "status": True,
                    "message": "Success",
                    "path": "/api/endpoint",
                    "data": {}
                }
            ]
        }
    }

# Auth-specific response models
class AuthData(BaseModel):
    """Authentication response data"""
    access_token: str = Field(..., description="JWT access token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    user_id: Optional[str] = Field(None, description="User ID", example="123e4567-e89b-12d3-a456-426614174000")
    email: Optional[str] = Field(None, description="User email", example="user@example.com")
    mobile: Optional[str] = Field(None, description="User mobile number", example="+1234567890")
    role: Optional[str] = Field(None, description="User role", example="admin")
    is_active: Optional[bool] = Field(None, description="User active status", example=True)
    first_name: Optional[str] = Field(None, description="User first name", example="John")
    last_name: Optional[str] = Field(None, description="User last name", example="Doe")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3OCIsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsImV4cCI6MTYxNjIzOTAyMn0...",
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "mobile": "+1234567890",
                    "role": "admin",
                    "is_active": True,
                    "first_name": "John",
                    "last_name": "Doe",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3OCIsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsImV4cCI6MTYxNjIzOTAyMn0..."
                }
            ]
        }
    }

class UserData(BaseModel):
    """User information data"""
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    mobile: Optional[str] = Field(None, description="User mobile number")
    role: Optional[str] = Field(None, description="User role")
    is_active: bool = Field(..., description="User active status")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    username: Optional[str] = Field(None, description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "mobile": "+1234567890",
                    "role": "admin",
                    "is_active": True,
                    "first_name": "John",
                    "last_name": "Doe",
                    "username": "johndoe",
                    "full_name": "John Doe"
                }
            ]
        }
    }

