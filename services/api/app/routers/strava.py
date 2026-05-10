from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.security import decrypt_token, encrypt_token, get_client_key, webhook_limiter
from app.models.tables import Activity, AuditEvent, Participant
from app.services.campaign import (
    get_active_campaign,
    is_activity_eligible,
    meters_to_miles,
)
from app.services.strava import StravaClient, strava_expires_at

router = APIRouter(prefix="/strava", tags=["strava"])


@router.get("/oauth/start")
async def oauth_start(invite: str = Query(...)) -> RedirectResponse:
    return RedirectResponse(StravaClient().authorization_url(invite))


@router.get("/oauth/callback")
async def oauth_callback(
    code: str,
    state: str,
    session: AsyncSession | None = Depends(get_db_session),
) -> RedirectResponse:
    if session is None:
        return RedirectResponse(f"{get_settings().app_url.rstrip('/')}/admin?strava=no-db")

    participant = (
        await session.execute(select(Participant).where(Participant.invite_token == state))
    ).scalar_one_or_none()
    if participant is None:
        raise HTTPException(status_code=404, detail="Invite token not found")

    token_payload = await StravaClient().exchange_code(code)
    athlete = token_payload.get("athlete", {})
    participant.strava_athlete_id = athlete.get("id")
    participant.strava_refresh_token = encrypt_token(token_payload["refresh_token"])
    participant.strava_access_token = encrypt_token(token_payload["access_token"])
    participant.strava_token_expires_at = strava_expires_at(token_payload["expires_at"])
    participant.connection_status = "connected"
    await session.commit()

    return RedirectResponse(f"{get_settings().app_url.rstrip('/')}/admin?strava=connected")


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> dict[str, str]:
    if hub_mode == "subscribe" and hub_verify_token == get_settings().strava_verify_token:
        return {"hub.challenge": hub_challenge}
    raise HTTPException(status_code=403, detail="Invalid Strava verification token")


@router.post("/webhook")
async def strava_webhook(
    request: Request,
    session: AsyncSession | None = Depends(get_db_session),
) -> dict[str, bool]:
    webhook_limiter.check(get_client_key(request))
    payload = await request.json()

    if session is not None:
        await process_strava_event(session, payload)

    return {"received": True}


async def process_strava_event(session: AsyncSession, payload: dict) -> None:
    event_id = f"{payload.get('subscription_id')}:{payload.get('object_type')}:{payload.get('object_id')}:{payload.get('aspect_type')}:{payload.get('event_time')}"
    existing = (
        await session.execute(
            select(AuditEvent).where(
                AuditEvent.event_source == "strava",
                AuditEvent.event_id == event_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return

    session.add(
        AuditEvent(
            event_source="strava",
            event_id=event_id,
            action=payload.get("aspect_type", "unknown"),
            payload=payload,
        )
    )

    if payload.get("object_type") == "athlete" and payload.get("updates", {}).get("authorized") == "false":
        athlete_id = payload.get("owner_id")
        participant = (
            await session.execute(select(Participant).where(Participant.strava_athlete_id == athlete_id))
        ).scalar_one_or_none()
        if participant is not None:
            participant.connection_status = "revoked"
            participant.strava_access_token = None
            participant.strava_refresh_token = None

    if payload.get("object_type") == "activity":
        await sync_activity_from_strava(session, payload)

    await session.commit()


async def sync_activity_from_strava(session: AsyncSession, payload: dict) -> None:
    participant = (
        await session.execute(select(Participant).where(Participant.strava_athlete_id == payload.get("owner_id")))
    ).scalar_one_or_none()
    campaign = await get_active_campaign(session)
    if participant is None or campaign is None or not participant.strava_access_token:
        return

    if payload.get("aspect_type") == "delete":
        existing = (
            await session.execute(
                select(Activity).where(Activity.strava_activity_id == payload.get("object_id"))
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.inclusion_status = "deleted"
            existing.eligible = False
        return

    access_token = decrypt_token(participant.strava_access_token)
    client = StravaClient()
    activity = await client.get_activity(access_token, int(payload["object_id"]))
    started_at = parse_strava_datetime(activity.get("start_date"))
    sport_type = activity.get("sport_type") or activity.get("type") or "Unknown"
    distance_miles = meters_to_miles(activity.get("distance", 0))
    eligible = is_activity_eligible(sport_type, started_at, campaign.starts_at, campaign.ends_at)

    existing = (
        await session.execute(select(Activity).where(Activity.strava_activity_id == activity["id"]))
    ).scalar_one_or_none()
    if existing is None:
        session.add(
            Activity(
                campaign_id=campaign.id,
                participant_id=participant.id,
                strava_activity_id=activity["id"],
                distance_miles=distance_miles,
                sport_type=sport_type,
                started_at=started_at,
                eligible=eligible,
                inclusion_status="included" if eligible else "excluded",
            )
        )
    else:
        existing.distance_miles = distance_miles
        existing.sport_type = sport_type
        existing.started_at = started_at
        existing.eligible = eligible
        existing.inclusion_status = "included" if eligible else "excluded"


def parse_strava_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

