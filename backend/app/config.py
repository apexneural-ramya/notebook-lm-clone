"""Configuration settings for the backend application"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory only
# This ensures we always use backend/.env
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / '.env'
load_dotenv(dotenv_path=env_file)

# Database
# Ensure DATABASE_URL uses asyncpg driver
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))
DATABASE_NAME = os.getenv("DATABASE_NAME", "notebooklm")
DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")

# Build DATABASE_URL from components or use full URL
# Priority: .env file > environment variable > default
# Use override=False to prioritize .env file over system env vars
_raw_db_url = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)
# If DATABASE_URL was loaded from .env file, it should already be set correctly
# But if it came from system env var, we need to check if it matches our expected database
# Force use of DATABASE_NAME from .env if DATABASE_URL doesn't match
if _raw_db_url and DATABASE_NAME not in _raw_db_url:
    # Rebuild URL using DATABASE_NAME from .env file
    import re
    _raw_db_url = re.sub(r'/([^/]+)(?:\?|$)', f'/{DATABASE_NAME}', _raw_db_url)

# Force asyncpg driver if not present
if "+asyncpg" not in _raw_db_url:
    if _raw_db_url.startswith("postgresql://"):
        DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif _raw_db_url.startswith("postgres://"):
        DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        import re
        DATABASE_URL = re.sub(r'postgresql\+[^:]+://', 'postgresql+asyncpg://', _raw_db_url)
else:
    DATABASE_URL = _raw_db_url

# JWT Settings
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "your-super-secret-key-change-in-production-please-use-a-strong-random-key"
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# CORS Settings
# Comma-separated list of allowed origins (must be set in environment)
# Production example: "https://app.example.com,https://www.example.com"
# Development example: "http://localhost:3000,http://127.0.0.1:3000"
# Must be explicitly configured via BACKEND_CORS_ORIGINS environment variable
# Note: Using BACKEND_CORS_ORIGINS to avoid conflict with Apex framework's CORS_ORIGINS (which expects JSON)
BACKEND_CORS_ORIGINS_STR = os.getenv("BACKEND_CORS_ORIGINS", "")
CORS_ORIGINS = [origin.strip() for origin in BACKEND_CORS_ORIGINS_STR.split(",") if origin.strip()] if BACKEND_CORS_ORIGINS_STR else []

# Backend Server Settings
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

# Frontend URL (for redirects, etc.)
# Format: https://yourdomain.com (production)
# Must be set in backend/.env for production use
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

