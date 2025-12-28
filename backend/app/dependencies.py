"""FastAPI dependencies for authentication"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.models.user import User
from app.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Verify JWT token and return current user"""
    token = credentials.credentials
    
    try:
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        token_type = payload.get("type")
        if token_type != "access":
            logger.warning(f"Invalid token type: {token_type}, expected 'access'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token payload missing 'sub' (user_id)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        logger.debug(f"Getting user with ID: {user_id} (type: {type(user_id)})")
        
        # Get user from database using Apex's get_user function
        # Apex handles async internally, so we call it synchronously
        # Try to convert user_id to UUID if it's a string
        from apex import get_user
        try:
            # Apex's get_user might accept string or UUID, try both
            if isinstance(user_id, str):
                # Try as string first
                user = get_user(user_id)
                if not user:
                    # If that fails, try converting to UUID
                    from uuid import UUID
                    try:
                        uuid_obj = UUID(user_id)
                        user = get_user(uuid_obj)
                    except (ValueError, TypeError):
                        pass
            else:
                user = get_user(user_id)
        except Exception as get_user_error:
            logger.error(
                f"Error calling get_user with user_id: {user_id}",
                exc_info=True,
                extra={
                    "user_id": user_id,
                    "user_id_type": type(user_id).__name__,
                    "error": str(get_user_error)
                }
            )
            user = None
        
        if not user:
            logger.error(f"User not found in database for user_id: {user_id} (type: {type(user_id)})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        logger.debug(f"User found: {user.email if hasattr(user, 'email') else 'unknown'}")
        
        # Check if user is active
        if hasattr(user, 'is_active') and not user.is_active:
            logger.warning(f"User account is inactive: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in get_current_user: {str(e)}",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )
