from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CampaignPublic(BaseModel):
    name: str
    slug: str
    beneficiary: str
    mission: str
    dollarsPerMile: float
    startsAt: datetime
    endsAt: datetime


class CampaignTotals(BaseModel):
    dollarsRaised: float
    milesPledged: float
    milesCompleted: float
    milesRemaining: float
    completionPercent: float
    nextMilestoneMiles: int


class ParticipantPublic(BaseModel):
    id: str
    name: str
    role: str
    initials: str
    bio: str
    avatarUrl: str | None = None


class DonationPublic(BaseModel):
    id: str
    donorName: str
    message: str
    amount: float
    createdAt: datetime


class CampaignSnapshot(BaseModel):
    campaign: CampaignPublic
    totals: CampaignTotals
    participants: list[ParticipantPublic]
    donations: list[DonationPublic]


class CreatePayPalOrderRequest(BaseModel):
    amount: Decimal = Field(gt=0, le=100_000)
    donor_name: str | None = Field(default=None, max_length=160)
    message: str | None = Field(default=None, max_length=240)
    anonymous: bool = True


class PayPalOrderResponse(BaseModel):
    id: str
    approve_url: str | None = None


class AdminLoginRequest(BaseModel):
    password: str


class ManualAdjustmentRequest(BaseModel):
    dollars_delta: Decimal = Decimal("0")
    miles_delta: Decimal = Decimal("0")
    reason: str = Field(min_length=3, max_length=240)


class StravaOAuthCallback(BaseModel):
    code: str
    state: str


class ManualAdjustmentResponse(BaseModel):
    ok: bool
    audit_id: UUID | None = None

