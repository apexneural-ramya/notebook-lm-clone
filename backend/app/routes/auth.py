"""Authentication routes using Apex"""
import secrets
import traceback
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from apex.auth import signup, login
from apex import get_user
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy import text, select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.logger import get_logger
from app.config import (
    JWT_SECRET_KEY, 
    JWT_ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    DATABASE_URL
)
from app.dependencies import get_current_user
from app.schemas import StandardResponse, AuthData, UserData
from app.models.user import User
from passlib.context import CryptContext

# Password hashing context (same as Apex uses)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Logger
logger = get_logger(__name__)

router = APIRouter()

# Token creation functions
def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# Request/Response models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/signup", response_model=StandardResponse)
async def signup_endpoint(request: SignupRequest):
    """User signup endpoint"""
    try:
        # Validate password complexity
        if len(request.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        
        # Call Apex signup (NO await - Apex handles async internally)
        user = signup(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            username=request.username
        )
        
        # Extract user info
        user_id = str(user.id) if hasattr(user, 'id') else None
        email = user.email if hasattr(user, 'email') else request.email
        
        # Get full_name and ensure it's a string (not boolean or other type)
        full_name_raw = getattr(user, 'full_name', request.full_name)
        if isinstance(full_name_raw, bool):
            # If full_name is a boolean, use the request value or None
            full_name = request.full_name if request.full_name else None
        elif isinstance(full_name_raw, str) and full_name_raw.strip():
            full_name = full_name_raw.strip()
        else:
            full_name = request.full_name if request.full_name else None
        
        username = getattr(user, 'username', request.username)
        is_active = getattr(user, 'is_active', True)
        is_superuser = getattr(user, 'is_superuser', False)
        
        # Parse full_name into first_name and last_name if available
        first_name = None
        last_name = None
        if full_name and isinstance(full_name, str):
            name_parts = full_name.split(maxsplit=1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
        
        # Generate custom tokens
        token_data = {"sub": user_id, "email": email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Build auth data response
        auth_data = AuthData(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            email=email,
            mobile=None,  # Not in current User model
            role="admin" if is_superuser else "user",
            is_active=is_active,
            first_name=first_name,
            last_name=last_name
        )
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="Account created successfully",
            path="/api/auth/signup",
            data=auth_data
        )
        
    except ValueError as e:
        error_msg = str(e)
        # Log detailed error
        logger.error(f"Signup validation error: {error_msg}", exc_info=True)
        
        if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail="An account with this email already exists. Please use a different email or try logging in."
            )
        raise HTTPException(
            status_code=400,
            detail="Invalid input. Please check your information and try again."
        )
    except Exception as e:
        # Log full error details to file
        logger.error(
            f"Signup failed for email: {request.email}",
            exc_info=True,
            extra={
                "email": request.email,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
        )
        # Return user-friendly message
        raise HTTPException(
            status_code=500,
            detail="Unable to create account at this time. Please try again later."
        )

@router.post("/login", response_model=StandardResponse)
async def login_endpoint(request: LoginRequest):
    """User login endpoint"""
    try:
        # Call Apex login (NO await)
        try:
            result = login(email=request.email, password=request.password)
        except Exception as apex_error:
            # Log Apex-specific errors
            error_msg = str(apex_error)
            logger.warning(f"Apex login error for email: {request.email} - {error_msg}")
            
            # Check if it's an authentication error
            if "not authenticated" in error_msg.lower() or "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password. Please check your credentials and try again."
                )
            # Re-raise as ValueError to be caught by outer handler
            raise ValueError(error_msg) from apex_error
        
        # Log the result type for debugging
        logger.debug(f"Login result type: {type(result)}, result: {result if isinstance(result, dict) else 'Not a dict'}")
        
        # Apex returns dict with tokens: {'access_token': '...', 'refresh_token': '...', 'token_type': 'bearer'}
        if isinstance(result, dict) and 'access_token' in result:
            # Decode Apex token to extract user_id (without verification)
            apex_payload = jwt.decode(
                result['access_token'],
                "",
                options={"verify_signature": False}
            )
            user_id = apex_payload.get('sub', '')
            email = apex_payload.get('email', request.email)
            
            # Get user details from database
            from apex import get_user
            user = get_user(user_id)
            
            # Extract user info
            # Get full_name and ensure it's a string (not boolean or other type)
            full_name_raw = getattr(user, 'full_name', None) if user else None
            if isinstance(full_name_raw, bool):
                # If full_name is a boolean, use None
                full_name = None
            elif isinstance(full_name_raw, str) and full_name_raw.strip():
                full_name = full_name_raw.strip()
            else:
                full_name = None
            
            username = getattr(user, 'username', None) if user else None
            is_active = getattr(user, 'is_active', True) if user else True
            is_superuser = getattr(user, 'is_superuser', False) if user else False
            
            # Parse full_name into first_name and last_name if available
            first_name = None
            last_name = None
            if full_name and isinstance(full_name, str):
                name_parts = full_name.split(maxsplit=1)
                first_name = name_parts[0] if len(name_parts) > 0 else None
                last_name = name_parts[1] if len(name_parts) > 1 else None
            
            # Generate OUR custom tokens
            token_data = {"sub": user_id, "email": email}
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
            # Build auth data response
            auth_data = AuthData(
                access_token=access_token,
                refresh_token=refresh_token,
                user_id=user_id,
                email=email,
                mobile=None,  # Not in current User model
                role="admin" if is_superuser else "user",
                is_active=is_active,
                first_name=first_name,
                last_name=last_name
            )
            
            return StandardResponse(
                status_code=200,
                status=True,
                message="Login successful",
                path="/api/auth/login",
                data=auth_data
            )
        else:
            # Log what we actually got
            logger.error(
                f"Unexpected login response format for email: {request.email}",
                extra={
                    "result_type": type(result).__name__,
                    "result": str(result)[:200] if result else None
                }
            )
            raise HTTPException(
                status_code=500, 
                detail="Unexpected login response format. Please try again or contact support."
            )
            
    except ValueError as e:
        # Log authentication failure (without password)
        logger.warning(f"Login failed for email: {request.email} - Invalid credentials")
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password. Please check your credentials and try again."
        )
    except Exception as e:
        # Log full error details to file
        logger.error(
            f"Login error for email: {request.email}",
            exc_info=True,
            extra={
                "email": request.email,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
        )
        # Return user-friendly message
        raise HTTPException(
            status_code=500,
            detail="Unable to sign in at this time. Please try again later."
        )

@router.get("/me", response_model=StandardResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    try:
        logger.debug(f"get_current_user_info called for user: {current_user.email if hasattr(current_user, 'email') else 'unknown'}")
        
        # Get full_name and ensure it's a string (not boolean or other type)
        full_name_raw = getattr(current_user, 'full_name', None)
        if isinstance(full_name_raw, bool):
            # If full_name is a boolean, use None
            full_name = None
        elif isinstance(full_name_raw, str) and full_name_raw.strip():
            full_name = full_name_raw.strip()
        else:
            full_name = None
        
        # Get username and ensure it's a string (not boolean or other type)
        username_raw = getattr(current_user, 'username', None)
        if isinstance(username_raw, bool):
            # If username is a boolean, use None
            username = None
        elif isinstance(username_raw, str) and username_raw.strip():
            username = username_raw.strip()
        else:
            username = None
        
        is_active = getattr(current_user, 'is_active', True)
        is_superuser = getattr(current_user, 'is_superuser', False)
        
        # Parse full_name into first_name and last_name if available
        first_name = None
        last_name = None
        if full_name and isinstance(full_name, str):
            name_parts = full_name.split(maxsplit=1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
        
        user_data = UserData(
            user_id=str(current_user.id),
            email=current_user.email,
            mobile=None,  # Not in current User model
            role="admin" if is_superuser else "user",
            is_active=is_active,
            first_name=first_name,
            last_name=last_name,
            username=username,
            full_name=full_name
        )
        
        logger.debug(f"Successfully retrieved user info for: {current_user.email}")
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="User retrieved successfully",
            path="/api/auth/me",
            data=user_data
        )
    except Exception as e:
        logger.error(
            f"Error in get_current_user_info: {str(e)}",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve user information. Please try again later."
        )

@router.post("/refresh", response_model=StandardResponse)
async def refresh_token_endpoint(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        # Decode refresh token
        payload = jwt.decode(
            request.refresh_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        email = payload.get("email")
        
        # Get user details from database
        from apex import get_user
        user = get_user(user_id) if user_id else None
        
        # Extract user info
        full_name = getattr(user, 'full_name', None) if user else None
        is_active = getattr(user, 'is_active', True) if user else True
        is_superuser = getattr(user, 'is_superuser', False) if user else False
        
        # Parse full_name into first_name and last_name if available
        first_name = None
        last_name = None
        if full_name:
            name_parts = full_name.split(maxsplit=1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None
        
        # Generate new tokens
        token_data = {"sub": user_id, "email": email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Build auth data response
        auth_data = AuthData(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user_id,
            email=email,
            mobile=None,  # Not in current User model
            role="admin" if is_superuser else "user",
            is_active=is_active,
            first_name=first_name,
            last_name=last_name
        )
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="Token refreshed successfully",
            path="/api/auth/refresh",
            data=auth_data
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")

@router.post("/forgot-password", response_model=StandardResponse)
async def forgot_password_endpoint(request: ForgotPasswordRequest):
    """Forgot password endpoint - generates reset token"""
    try:
        # Get user by email using direct database query
        sync_db_url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_db_url)
        Session = sessionmaker(bind=engine)
        
        user = None
        with Session() as session:
            result = session.execute(select(User).where(User.email == request.email))
            user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if user exists for security
            return StandardResponse(
                status_code=200,
                status=True,
                message="If the email exists, a password reset link has been sent",
                path="/api/auth/forgot-password",
                data=None
            )
        
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        
        # Store reset token in database using sync connection
        # Reuse the same engine and Session from above
        with Session() as session:
            # Invalidate any existing unused tokens for this user
            session.execute(text("""
                UPDATE password_reset_tokens 
                SET used = TRUE 
                WHERE user_id = :user_id AND used = FALSE
            """), {"user_id": str(user.id)})
            
            # Insert new reset token
            session.execute(text("""
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (:user_id, :token, :expires_at)
            """), {
                "user_id": str(user.id),
                "token": reset_token,
                "expires_at": expires_at
            })
            
            session.commit()
        
        # In production, send email with reset link
        # For now, return token in response (remove in production!)
        return StandardResponse(
            status_code=200,
            status=True,
            message="Password reset token generated. Check your email for reset instructions.",
            path="/api/auth/forgot-password",
            data={"reset_token": reset_token}  # Remove this in production - send via email only
        )
        
    except Exception as e:
        # Don't reveal if user exists
        return StandardResponse(
            status_code=200,
            status=True,
            message="If the email exists, a password reset link has been sent",
            path="/api/auth/forgot-password",
            data=None
        )

@router.post("/reset-password", response_model=StandardResponse)
async def reset_password_endpoint(request: ResetPasswordRequest):
    """Reset password endpoint - validates token and updates password"""
    try:
        # Validate password complexity
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        
        # Check password complexity
        has_upper = any(c.isupper() for c in request.new_password)
        has_lower = any(c.islower() for c in request.new_password)
        has_digit = any(c.isdigit() for c in request.new_password)
        
        if not (has_upper and has_lower and has_digit):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one uppercase letter, one lowercase letter, and one number"
            )
        
        # Verify reset token using sync database connection
        sync_db_url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_db_url)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Get token from database
            result = session.execute(text("""
                SELECT user_id, expires_at, used
                FROM password_reset_tokens
                WHERE token = :token
            """), {"token": request.token})
            
            token_data = result.fetchone()
            
            if not token_data:
                raise HTTPException(status_code=400, detail="Invalid or expired reset token")
            
            user_id, expires_at, used = token_data
            
            # Check if token is used
            if used:
                raise HTTPException(status_code=400, detail="Reset token has already been used")
            
            # Check if token is expired
            if datetime.utcnow() > expires_at:
                raise HTTPException(status_code=400, detail="Reset token has expired")
            
            # Get user
            user = get_user(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update password using Apex's password hashing
            # Hash the new password
            password_hash = pwd_context.hash(request.new_password)
            
            # Update user password
            session.execute(text("""
                UPDATE users
                SET password_hash = :password_hash, updated_at = NOW()
                WHERE id = :user_id
            """), {
                "password_hash": password_hash,
                "user_id": user_id
            })
            
            # Mark token as used
            session.execute(text("""
                UPDATE password_reset_tokens
                SET used = TRUE
                WHERE token = :token
            """), {"token": request.token})
            
            session.commit()
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="Password reset successfully",
            path="/api/auth/reset-password",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password reset failed: {str(e)}")

@router.post("/change-password", response_model=StandardResponse)
async def change_password_endpoint(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """Change password endpoint - requires authentication"""
    try:
        # Validate new password complexity
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        
        # Check password complexity
        has_upper = any(c.isupper() for c in request.new_password)
        has_lower = any(c.islower() for c in request.new_password)
        has_digit = any(c.isdigit() for c in request.new_password)
        
        if not (has_upper and has_lower and has_digit):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one uppercase letter, one lowercase letter, and one number"
            )
        
        # Verify old password by attempting login
        try:
            login_result = login(email=current_user.email, password=request.old_password)
            if not login_result or 'access_token' not in login_result:
                raise HTTPException(status_code=400, detail="Current password is incorrect")
        except ValueError:
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Hash the new password
        password_hash = pwd_context.hash(request.new_password)
        
        # Update password in database using sync connection
        sync_db_url = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_db_url)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            session.execute(text("""
                UPDATE users
                SET password_hash = :password_hash, updated_at = NOW()
                WHERE id = :user_id
            """), {
                "password_hash": password_hash,
                "user_id": str(current_user.id)
            })
            
            session.commit()
        
        return StandardResponse(
            status_code=200,
            status=True,
            message="Password changed successfully",
            path="/api/auth/change-password",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")

