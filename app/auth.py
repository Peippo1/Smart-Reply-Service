"""
Simple API key authentication dependency.
"""

import os

from fastapi import Depends, Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    """
    Validate the x-api-key header against the configured API_KEY env var.
    Raises 500 if API_KEY is not configured to avoid silent misconfiguration.
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured",
        )
    if x_api_key != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return None
