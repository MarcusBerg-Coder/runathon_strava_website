from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, campaign, paypal, strava

app = FastAPI(
    title="Runathon API",
    version="0.1.0",
    description="Campaign, donation, and activity APIs for the AEPI Runathon site.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(campaign.router)
app.include_router(paypal.router)
app.include_router(strava.router)
app.include_router(admin.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

