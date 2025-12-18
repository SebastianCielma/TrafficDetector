import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.app.core.config import settings

api_key_header_scheme = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header_scheme)) -> str:
    """Verify API key using constant-time comparison to prevent timing attacks."""
    if api_key is not None and secrets.compare_digest(api_key, settings.API_KEY):
        return api_key

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )
