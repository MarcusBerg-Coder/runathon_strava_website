from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import Activity, AuditEvent, Campaign, Donation, Participant
from app.schemas import (
    CampaignPublic,
    CampaignSnapshot,
    CampaignTotals,
    DonationPublic,
    ParticipantPublic,
)

ELIGIBLE_SPORT_TYPES = {"Run", "TrailRun", "Walk", "Hike"}
METERS_PER_MILE = Decimal("1609.344")


def decimal_to_float(value: Decimal | int | float | None, places: str = "0.1") -> float:
    if value is None:
        value = Decimal("0")
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return float(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def meters_to_miles(distance_meters: int | float | Decimal) -> Decimal:
    return (Decimal(str(distance_meters)) / METERS_PER_MILE).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )


def is_activity_eligible(
    sport_type: str,
    started_at: datetime,
    campaign_starts_at: datetime,
    campaign_ends_at: datetime,
) -> bool:
    if sport_type not in ELIGIBLE_SPORT_TYPES:
        return False
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    return campaign_starts_at <= started_at <= campaign_ends_at


def calculate_totals(
    dollars_raised: Decimal,
    dollars_per_mile: Decimal,
    miles_completed: Decimal,
) -> CampaignTotals:
    if dollars_per_mile <= 0:
        dollars_per_mile = Decimal("10")

    miles_pledged = dollars_raised / dollars_per_mile
    miles_remaining = max(Decimal("0"), miles_pledged - miles_completed)
    completion_percent = Decimal("0")
    if miles_pledged > 0:
        completion_percent = min(Decimal("100"), (miles_completed / miles_pledged) * Decimal("100"))

    next_milestone = max(10, int(ceil(float(miles_pledged) / 25.0) * 25))

    return CampaignTotals(
        dollarsRaised=decimal_to_float(dollars_raised, "0.01"),
        milesPledged=decimal_to_float(miles_pledged, "0.1"),
        milesCompleted=decimal_to_float(miles_completed, "0.1"),
        milesRemaining=decimal_to_float(miles_remaining, "0.1"),
        completionPercent=decimal_to_float(completion_percent, "0.1"),
        nextMilestoneMiles=next_milestone,
    )


def fallback_snapshot() -> CampaignSnapshot:
    starts = datetime(2026, 5, 1, tzinfo=timezone.utc)
    ends = datetime(2026, 6, 1, tzinfo=timezone.utc)
    totals = calculate_totals(Decimal("1840"), Decimal("10"), Decimal("71.6"))
    return CampaignSnapshot(
        campaign=CampaignPublic(
            name="AEPI Runathon",
            slug="aepi-runathon",
            beneficiary="Chapter philanthropy partner",
            mission="Brothers are turning every donation into miles for a cause our chapter is proud to support.",
            dollarsPerMile=10,
            startsAt=starts,
            endsAt=ends,
        ),
        totals=totals,
        participants=[
            ParticipantPublic(
                id="sample-noah",
                name="Noah Cohen",
                role="Run captain",
                initials="NC",
                bio="Coordinates weekly group runs and keeps the board honest.",
            ),
            ParticipantPublic(
                id="sample-eli",
                name="Eli Rosen",
                role="Distance lead",
                initials="ER",
                bio="Logs long efforts and recruits brothers for weekend mileage.",
            ),
            ParticipantPublic(
                id="sample-sam",
                name="Sam Levine",
                role="Outreach",
                initials="SL",
                bio="Connects donors with the mission behind every mile.",
            ),
        ],
        donations=[
            DonationPublic(
                id="sample-1",
                donorName="Anonymous",
                message="Run hard for a good cause.",
                amount=100,
                createdAt=datetime(2026, 5, 9, 16, 30, tzinfo=timezone.utc),
            ),
            DonationPublic(
                id="sample-2",
                donorName="The Goldberg Family",
                message="Proud of the brothers.",
                amount=180,
                createdAt=datetime(2026, 5, 8, 19, 10, tzinfo=timezone.utc),
            ),
        ],
    )


async def get_active_campaign(session: AsyncSession | None) -> Campaign | None:
    if session is None:
        return None

    result = await session.execute(select(Campaign).where(Campaign.active.is_(True)).limit(1))
    return result.scalar_one_or_none()


async def get_current_snapshot(session: AsyncSession | None) -> CampaignSnapshot:
    campaign = await get_active_campaign(session)
    if campaign is None or session is None:
        return fallback_snapshot()

    donation_total = await session.scalar(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.campaign_id == campaign.id,
            Donation.status == "completed",
        )
    )
    miles_total = await session.scalar(
        select(func.coalesce(func.sum(Activity.distance_miles), 0)).where(
            Activity.campaign_id == campaign.id,
            Activity.eligible.is_(True),
            Activity.inclusion_status == "included",
        )
    )

    participant_rows = (
        await session.execute(
            select(Participant)
            .where(Participant.campaign_id == campaign.id)
            .order_by(Participant.created_at.asc())
            .limit(12)
        )
    ).scalars()

    donation_rows = (
        await session.execute(
            select(Donation)
            .where(Donation.campaign_id == campaign.id, Donation.status == "completed")
            .order_by(Donation.completed_at.desc().nullslast(), Donation.created_at.desc())
            .limit(6)
        )
    ).scalars()

    return CampaignSnapshot(
        campaign=CampaignPublic(
            name=campaign.name,
            slug=campaign.slug,
            beneficiary=campaign.beneficiary,
            mission=campaign.mission,
            dollarsPerMile=decimal_to_float(campaign.dollars_per_mile, "0.01"),
            startsAt=campaign.starts_at,
            endsAt=campaign.ends_at,
        ),
        totals=calculate_totals(
            Decimal(str(donation_total or 0)),
            campaign.dollars_per_mile,
            Decimal(str(miles_total or 0)),
        ),
        participants=[
            ParticipantPublic(
                id=str(participant.id),
                name=participant.name,
                role=participant.role,
                initials=participant.initials,
                bio=participant.bio,
                avatarUrl=participant.avatar_url,
            )
            for participant in participant_rows
        ],
        donations=[
            DonationPublic(
                id=str(donation.id),
                donorName="Anonymous" if donation.anonymous else donation.donor_name or "Anonymous",
                message=donation.donor_message or "Proud to support the runathon.",
                amount=decimal_to_float(donation.amount, "0.01"),
                createdAt=donation.completed_at or donation.created_at,
            )
            for donation in donation_rows
        ],
    )


async def record_manual_adjustment(
    session: AsyncSession | None,
    dollars_delta: Decimal,
    miles_delta: Decimal,
    reason: str,
) -> str | None:
    if session is None:
        return None

    campaign = await get_active_campaign(session)
    if campaign is None:
        return None

    event = AuditEvent(
        event_source="admin",
        event_id=f"manual-{uuid4()}",
        action="manual_adjustment",
        payload={
            "campaign_id": str(campaign.id),
            "dollars_delta": str(dollars_delta),
            "miles_delta": str(miles_delta),
            "reason": reason,
        },
    )
    session.add(event)

    if dollars_delta:
        session.add(
            Donation(
                campaign_id=campaign.id,
                amount=dollars_delta,
                status="completed",
                donor_name="Manual adjustment",
                donor_message=reason,
                anonymous=False,
                completed_at=datetime.now(timezone.utc),
            )
        )

    if miles_delta:
        participant = (
            await session.execute(
                select(Participant).where(Participant.campaign_id == campaign.id).limit(1)
            )
        ).scalar_one_or_none()
        if participant is not None:
            session.add(
                Activity(
                    campaign_id=campaign.id,
                    participant_id=participant.id,
                    strava_activity_id=abs(hash(str(event.id))) % 2_000_000_000,
                    distance_miles=miles_delta,
                    sport_type="Manual",
                    started_at=datetime.now(timezone.utc),
                    eligible=True,
                    inclusion_status="included",
                )
            )

    await session.commit()
    return str(event.id)

