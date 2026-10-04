from __future__ import annotations

import os
import time
from collections import OrderedDict
from secrets import token_urlsafe

from starlette.responses import JSONResponse

from .store import DATA_DIR

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 512 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".pdf", ".docx", ".py", ".js", ".ts", ".tsx"}


def is_production() -> bool:
    return os.getenv("APP_ENV") == "production" or os.getenv("RENDER", "").lower() == "true"


def session_secret() -> str:
    secret = os.getenv("SESSION_SECRET", "")
    valid = len(secret) >= 32 and not any(word in secret.lower() for word in ("change-me", "generate-a", "your-secret"))
    if is_production():
        if not valid:
            raise RuntimeError("Set a random SESSION_SECRET of at least 32 characters in production.")
        if os.getenv("SESSION_COOKIE_SECURE", "false").lower() != "true":
            raise RuntimeError("Production requires SESSION_COOKIE_SECURE=true.")
        if os.getenv("DEV_AUTH_ENABLED", "false").lower() == "true" or os.getenv("ALLOW_GUEST_PROJECTS", "false").lower() == "true":
            raise RuntimeError("Development sign-in and guest projects must be disabled in production.")
        if not os.getenv("DATABASE_URL"):
            raise RuntimeError("Set DATABASE_URL to a dedicated external PostgreSQL database in production.")
    if valid:
        return secret
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / ".session-secret"
    try:
        with path.open("x", encoding="utf-8") as file:
            path.chmod(0o600)
            file.write(token_urlsafe(48))
    except FileExistsError:
        pass
    return path.read_text(encoding="utf-8").strip()


class RequestLimitsMiddleware:
    """Bound request memory and per-process write traffic before parsing bodies."""

    def __init__(self, app, allowed_origins):
        self.app = app
        self.allowed_origins = set(allowed_origins)
        self.windows = OrderedDict()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode()
        if origin and origin not in self.allowed_origins:
            return await JSONResponse({"detail": "Origin not allowed."}, status_code=403)(scope, receive, send)
        identity = scope.get("session", {}).get("user_id") or (scope.get("client") or ("unknown",))[0]
        now = time.monotonic()
        start, count = self.windows.get(identity, (now, 0))
        if now - start >= 60:
            start, count = now, 0
        self.windows[identity] = (start, count + 1)
        self.windows.move_to_end(identity)
        if len(self.windows) > 10000:
            self.windows.popitem(last=False)
        if count >= 30:
            return await JSONResponse({"detail": "Too many requests. Try again shortly."}, status_code=429, headers={"Retry-After": "60"})(scope, receive, send)
        try:
            declared_size = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid content length."}, status_code=400)(scope, receive, send)
        if declared_size > MAX_REQUEST_BYTES:
            return await JSONResponse({"detail": "Request exceeds the upload limit."}, status_code=413)(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > MAX_REQUEST_BYTES:
                return await JSONResponse({"detail": "Request exceeds the upload limit."}, status_code=413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
