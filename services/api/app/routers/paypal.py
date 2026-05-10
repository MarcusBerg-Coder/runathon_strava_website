from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import donation_limiter, get_client_key, webhook_limiter
from app.models.tables import AuditEvent, Donation
from app.schemas import CreatePayPalOrderRequest, PayPalOrderResponse
from app.services.campaign import get_active_campaign
from app.services.paypal import PayPalClient, get_approve_url

router = APIRouter(prefix="/paypal", tags=["paypal"])


@router.post("/orders", response_model=PayPalOrderResponse)
async def create_order(
    payload: CreatePayPalOrderRequest,
    request: Request,
    session: AsyncSession | None = Depends(get_db_session),
) -> PayPalOrderResponse:
    donation_limiter.check(get_client_key(request))

    campaign = await get_active_campaign(session)
    donation_id = "pending-no-db"
    donation: Donation | None = None

    if campaign is not None and session is not None:
        donation = Donation(
            campaign_id=campaign.id,
            amount=payload.amount,
            status="pending",
            donor_name=payload.donor_name,
            donor_message=payload.message,
            anonymous=payload.anonymous,
        )
        session.add(donation)
        await session.flush()
        donation_id = str(donation.id)

    order = await PayPalClient().create_order(
        payload.amount,
        donation_id,
        payload.donor_name,
        payload.message,
    )

    if donation is not None and session is not None:
        donation.paypal_order_id = order["id"]
        await session.commit()

    return PayPalOrderResponse(id=order["id"], approve_url=get_approve_url(order))


@router.post("/orders/{order_id}/capture")
async def capture_order(
    order_id: str,
    session: AsyncSession | None = Depends(get_db_session),
) -> dict[str, str]:
    result = await PayPalClient().capture_order(order_id)
    capture = _first_capture(result)

    if session is not None:
        donation = (
            await session.execute(select(Donation).where(Donation.paypal_order_id == order_id))
        ).scalar_one_or_none()
        if donation is not None and capture is not None:
            donation.paypal_capture_id = capture.get("id")
            donation.status = "capture_pending"
            await session.commit()

    return {"status": "capture_submitted"}


@router.post("/webhook")
async def paypal_webhook(
    request: Request,
    session: AsyncSession | None = Depends(get_db_session),
) -> dict[str, bool]:
    webhook_limiter.check(get_client_key(request))
    event = await request.json()
    headers = {key.lower(): value for key, value in request.headers.items()}

    verified = await PayPalClient().verify_webhook(headers, event)
    if not verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PayPal webhook signature")

    if session is not None:
        await process_paypal_event(session, event)

    return {"received": True}


async def process_paypal_event(session: AsyncSession, event: dict) -> None:
    event_id = event.get("id")
    event_type = event.get("event_type", "unknown")
    if not event_id:
        raise HTTPException(status_code=400, detail="Missing PayPal event id")

    existing = (
        await session.execute(
            select(AuditEvent).where(
                AuditEvent.event_source == "paypal",
                AuditEvent.event_id == event_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    resource = event.get("resource", {})
    capture_id = resource.get("id")
    order_id = _related_order_id(resource)
    status_value = _donation_status_for_event(event_type)
    amount_value = _amount_from_resource(resource)

    donation = None
    if capture_id:
        donation = (
            await session.execute(select(Donation).where(Donation.paypal_capture_id == capture_id))
        ).scalar_one_or_none()
    if donation is None and order_id:
        donation = (
            await session.execute(select(Donation).where(Donation.paypal_order_id == order_id))
        ).scalar_one_or_none()

    if donation is not None:
        if capture_id:
            donation.paypal_capture_id = capture_id
        if amount_value is not None:
            donation.amount = amount_value
        donation.status = status_value
        if status_value == "completed":
            donation.completed_at = datetime.now(timezone.utc)

    session.add(
        AuditEvent(
            event_source="paypal",
            event_id=event_id,
            action=event_type,
            payload=event,
        )
    )
    await session.commit()


def _donation_status_for_event(event_type: str) -> str:
    match event_type:
        case "PAYMENT.CAPTURE.COMPLETED":
            return "completed"
        case "PAYMENT.CAPTURE.PENDING":
            return "capture_pending"
        case "PAYMENT.CAPTURE.DENIED" | "CHECKOUT.PAYMENT-APPROVAL.REVERSED":
            return "failed"
        case "CHECKOUT.ORDER.APPROVED":
            return "approved"
        case _:
            return "event_received"


def _related_order_id(resource: dict) -> str | None:
    supplementary = resource.get("supplementary_data", {})
    related = supplementary.get("related_ids", {})
    return related.get("order_id") or resource.get("id")


def _amount_from_resource(resource: dict) -> Decimal | None:
    amount = resource.get("amount", {})
    value = amount.get("value")
    if value is None:
        return None
    return Decimal(str(value))


def _first_capture(order: dict) -> dict | None:
    for unit in order.get("purchase_units", []):
        payments = unit.get("payments", {})
        captures = payments.get("captures", [])
        if captures:
            return captures[0]
    return None

