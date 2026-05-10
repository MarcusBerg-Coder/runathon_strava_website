import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Request, Response, status

from app.core.config import get_settings

SESSION_COOKIE = "runathon_admin"
SESSION_TTL_SECONDS = 60 * 60 * 8


def _sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def create_admin_session() -> str:
    settings = get_settings()
    payload = {
        "sub": "admin",
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
        "nonce": secrets.token_urlsafe(12),
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
    signature = _sign(raw.encode(), settings.admin_session_secret)
    return f"{raw}.{signature}"


def verify_admin_session(token: str | None) -> bool:
    if not token or "." not in token:
        return False

    settings = get_settings()
    raw, signature = token.rsplit(".", 1)
    expected = _sign(raw.encode(), settings.admin_session_secret)
    if not secrets.compare_digest(signature, expected):
        return False

    try:
        payload = json.loads(base64.urlsafe_b64decode(raw.encode()))
    except (ValueError, json.JSONDecodeError):
        return False

    return payload.get("sub") == "admin" and int(payload.get("exp", 0)) > int(time.time())


def set_admin_cookie(response: Response, token: str) -> None:
    secure_cookie = get_settings().app_url.startswith("https://")
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
    )


def clear_admin_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def require_admin(request: Request) -> None:
    if not verify_admin_session(request.cookies.get(SESSION_COOKIE)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin session required")


def verify_admin_password(password: str) -> bool:
    configured = get_settings().admin_password
    if not configured:
        return False
    return secrets.compare_digest(password, configured)


@dataclass
class InMemoryRateLimiter:
    limit: int
    window_seconds: int
    hits: dict[str, list[float]] = field(default_factory=dict)

    def check(self, key: str) -> None:
        now = time.monotonic()
        window_start = now - self.window_seconds
        bucket = [hit for hit in self.hits.get(key, []) if hit >= window_start]
        if len(bucket) >= self.limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")
        bucket.append(now)
        self.hits[key] = bucket


admin_limiter = InMemoryRateLimiter(limit=5, window_seconds=60)
donation_limiter = InMemoryRateLimiter(limit=10, window_seconds=60)
webhook_limiter = InMemoryRateLimiter(limit=120, window_seconds=60)


def get_client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def get_token_cipher() -> Fernet | None:
    key = get_settings().strava_token_encryption_key
    if not key:
        return None
    return Fernet(key.encode("utf-8"))


def encrypt_token(token: str) -> str:
    cipher = get_token_cipher()
    if cipher is None:
        return token
    return cipher.encrypt(token.encode("utf-8")).decode("utf-8")


def decrypt_token(token: str) -> str:
    cipher = get_token_cipher()
    if cipher is None:
        return token
    try:
        return cipher.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(status_code=500, detail="Stored Strava token could not be decrypted") from exc
