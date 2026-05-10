from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import (
    admin_limiter,
    clear_admin_cookie,
    create_admin_session,
    get_client_key,
    require_admin,
    set_admin_cookie,
    verify_admin_password,
)
from app.schemas import AdminLoginRequest, ManualAdjustmentRequest, ManualAdjustmentResponse
from app.services.campaign import record_manual_adjustment

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login")
async def login(payload: AdminLoginRequest, request: Request, response: Response) -> dict[str, bool]:
    admin_limiter.check(get_client_key(request))
    if not verify_admin_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin password")

    set_admin_cookie(response, create_admin_session())
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response) -> dict[str, bool]:
    clear_admin_cookie(response)
    return {"ok": True}


@router.post("/manual-adjustments", response_model=ManualAdjustmentResponse)
async def manual_adjustment(
    payload: ManualAdjustmentRequest,
    request: Request,
    session: AsyncSession | None = Depends(get_db_session),
) -> ManualAdjustmentResponse:
    require_admin(request)
    audit_id = await record_manual_adjustment(
        session,
        payload.dollars_delta,
        payload.miles_delta,
        payload.reason,
    )
    return ManualAdjustmentResponse(ok=True, audit_id=audit_id)

