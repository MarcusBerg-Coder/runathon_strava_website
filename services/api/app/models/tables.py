import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    beneficiary: Mapped[str] = mapped_column(String(240))
    mission: Mapped[str] = mapped_column(Text)
    dollars_per_mile: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("10.00"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(120), default="Runner")
    initials: Mapped[str] = mapped_column(String(8))
    bio: Mapped[str] = mapped_column(Text, default="")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    invite_token: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    strava_athlete_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    strava_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    strava_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    strava_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    connection_status: Mapped[str] = mapped_column(String(40), default="invited")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    campaign: Mapped[Campaign] = relationship()


class Donation(Base):
    __tablename__ = "donations"
    __table_args__ = (
        UniqueConstraint("paypal_order_id", name="uq_donations_paypal_order_id"),
        UniqueConstraint("paypal_capture_id", name="uq_donations_paypal_capture_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    paypal_order_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    paypal_capture_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    donor_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    donor_message: Mapped[str | None] = mapped_column(String(240), nullable=True)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("strava_activity_id", name="uq_activities_strava_activity_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    strava_activity_id: Mapped[int] = mapped_column(index=True)
    distance_miles: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    sport_type: Mapped[str] = mapped_column(String(80))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    inclusion_status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (UniqueConstraint("event_source", "event_id", name="uq_audit_source_event"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_source: Mapped[str] = mapped_column(String(80))
    event_id: Mapped[str] = mapped_column(String(160))
    action: Mapped[str] = mapped_column(String(120))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

