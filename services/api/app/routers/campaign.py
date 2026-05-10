from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas import CampaignSnapshot
from app.services.campaign import get_current_snapshot

router = APIRouter(prefix="/campaign", tags=["campaign"])


@router.get("/current", response_model=CampaignSnapshot)
async def current_campaign(session: AsyncSession | None = Depends(get_db_session)) -> CampaignSnapshot:
    return await get_current_snapshot(session)

