from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


class StravaClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _ensure_configured(self) -> None:
        if not self.settings.strava_client_id or not self.settings.strava_client_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Strava credentials are not configured",
            )

    def authorization_url(self, invite_token: str) -> str:
        self._ensure_configured()
        query = urlencode(
            {
                "client_id": self.settings.strava_client_id,
                "redirect_uri": f"{self.settings.public_api_base_url}/strava/oauth/callback",
                "response_type": "code",
                "approval_prompt": "auto",
                "scope": "read,activity:read",
                "state": invite_token,
            }
        )
        return f"https://www.strava.com/oauth/authorize?{query}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": self.settings.strava_client_id,
                    "client_secret": self.settings.strava_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": self.settings.strava_client_id,
                    "client_secret": self.settings.strava_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_activity(self, access_token: str, activity_id: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"https://www.strava.com/api/v3/activities/{activity_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()


def strava_expires_at(expires_at: int) -> datetime:
    return datetime.fromtimestamp(expires_at, tz=timezone.utc)
