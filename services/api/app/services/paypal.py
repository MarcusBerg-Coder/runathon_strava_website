from decimal import Decimal
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


class PayPalClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _ensure_configured(self) -> None:
        if not self.settings.paypal_client_id or not self.settings.paypal_client_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PayPal credentials are not configured",
            )

    async def get_access_token(self) -> str:
        self._ensure_configured()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.settings.paypal_base_url}/v1/oauth2/token",
                auth=(self.settings.paypal_client_id, self.settings.paypal_client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def create_order(
        self,
        amount: Decimal,
        donation_id: str,
        donor_name: str | None,
        message: str | None,
    ) -> dict[str, Any]:
        access_token = await self.get_access_token()
        app_url = self.settings.app_url.rstrip("/")
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "custom_id": donation_id,
                    "description": "AEPI Runathon philanthropy donation",
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{amount:.2f}",
                    },
                }
            ],
            "application_context": {
                "brand_name": "AEPI Runathon",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "PAY_NOW",
                "return_url": f"{app_url}/?payment=approved",
                "cancel_url": f"{app_url}/?payment=cancelled",
            },
        }
        if donor_name or message:
            payload["purchase_units"][0]["custom_id"] = donation_id

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.settings.paypal_base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def capture_order(self, order_id: str) -> dict[str, Any]:
        access_token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.settings.paypal_base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def verify_webhook(self, headers: dict[str, str], event: dict[str, Any]) -> bool:
        if not self.settings.paypal_webhook_id:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PayPal webhook ID is not configured",
            )

        access_token = await self.get_access_token()
        payload = {
            "auth_algo": headers.get("paypal-auth-algo"),
            "cert_url": headers.get("paypal-cert-url"),
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "webhook_id": self.settings.paypal_webhook_id,
            "webhook_event": event,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.settings.paypal_base_url}/v1/notifications/verify-webhook-signature",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json().get("verification_status") == "SUCCESS"


def get_approve_url(order: dict[str, Any]) -> str | None:
    for link in order.get("links", []):
        if link.get("rel") == "approve":
            return link.get("href")
    return None

