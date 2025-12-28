"""FastAPI application entry point with Apex integration"""
# CRITICAL: nest_asyncio MUST be imported and applied FIRST
import nest_asyncio
nest_asyncio.apply()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from apex import Client, set_default_client
from app.config import DATABASE_URL, CORS_ORIGINS
from app.models.user import User
from app.logger import setup_logging

# Setup logging
setup_logging()

# Import routes
from app.routes import auth, documents, chat, podcast

# Initialize Apex Client
apex_client = Client(database_url=DATABASE_URL, user_model=User)
set_default_client(apex_client)

# Store client globally for use in dependencies
_apex_client = apex_client

# Create FastAPI app
app = FastAPI(
    title="NotebookLM API",
    description="Backend API for NotebookLM with authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
# Log CORS origins for debugging
from app.logger import get_logger
logger = get_logger(__name__)

# CORS origins must be configured in environment variables
# Must be explicitly set via BACKEND_CORS_ORIGINS in backend/.env
# Production: "https://app.example.com,https://www.example.com"
# Development: "http://localhost:3000,http://127.0.0.1:3000"
# Note: Using BACKEND_CORS_ORIGINS to avoid conflict with Apex framework's CORS_ORIGINS (which expects JSON)
if not CORS_ORIGINS:
    logger.error("CORS origins not configured! Please set BACKEND_CORS_ORIGINS in backend/.env")
    raise ValueError(
        "CORS origins must be configured in backend/.env. "
        "Set BACKEND_CORS_ORIGINS as a comma-separated list of allowed origins. "
        "Production example: 'https://app.example.com,https://www.example.com' "
        "Development example: 'http://localhost:3000,http://127.0.0.1:3000'"
    )

logger.info(f"CORS origins configured: {CORS_ORIGINS}")

# Add middleware to log CORS requests for debugging
class CORSDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        if method == "OPTIONS":
            logger.info(f"OPTIONS preflight request - Origin: {origin}, Path: {path}, Allowed origins: {CORS_ORIGINS}")
            if origin and origin not in CORS_ORIGINS:
                logger.warning(f"OPTIONS request from disallowed origin: {origin}")
        
        response = await call_next(request)
        return response

# Add CORS debug middleware first
app.add_middleware(CORSDebugMiddleware)

# Then add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(podcast.router, prefix="/api/podcast", tags=["Podcast"])

@app.get("/")
async def root():
    return {"message": "NotebookLM API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running"""
    return {"status": "ok", "message": "Server is running"}

