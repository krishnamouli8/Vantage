"""
Authentication middleware for API key validation.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import settings

# Define API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Raises:
        HTTPException: If authentication is enabled and key is invalid
    """
    # If auth is not enabled, allow all requests
    if not settings.auth_enabled:
        return
    
    # If auth is enabled but no API key configured, reject all requests
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is enabled but no API key is configured"
        )
    
    # Check if API key is provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Verify API key matches
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
