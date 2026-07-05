from __future__ import annotations

import os
from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request
from starlette.responses import RedirectResponse

from .store import public_user, upsert_user


def frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://127.0.0.1:5173").rstrip("/")


def redirect_base_url() -> str:
    return os.getenv("OAUTH_REDIRECT_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def auth_providers() -> dict[str, dict[str, bool | str]]:
    return {
        "github": {
            "available": bool(os.getenv("GITHUB_CLIENT_ID") and os.getenv("GITHUB_CLIENT_SECRET")),
            "login_url": "/auth/github/login",
        },
        "google": {
            "available": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
            "login_url": "/auth/google/login",
        },
    }


def current_user_id(request: Request) -> str | None:
    return request.session.get("user_id")


def clear_session(request: Request) -> None:
    request.session.clear()


def _require_provider(provider: str) -> None:
    if not auth_providers()[provider]["available"]:
        raise HTTPException(status_code=503, detail=f"{provider.title()} OAuth is not configured.")


def _state_for(request: Request, provider: str) -> str:
    state = token_urlsafe(24)
    request.session["oauth_state"] = state
    request.session["oauth_provider"] = provider
    return state


def _validate_state(request: Request, provider: str, state: str | None) -> None:
    if not state:
        raise HTTPException(status_code=400, detail="Missing OAuth state.")
    if request.session.get("oauth_state") != state or request.session.get("oauth_provider") != provider:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")


def _finish_login(request: Request, profile: dict[str, str | None]) -> RedirectResponse:
    user = upsert_user(profile)
    request.session.pop("oauth_state", None)
    request.session.pop("oauth_provider", None)
    request.session["user_id"] = user["id"]
    return RedirectResponse(f"{frontend_url()}/#live-case")


def github_login(request: Request) -> RedirectResponse:
    _require_provider("github")
    params = {
        "client_id": os.environ["GITHUB_CLIENT_ID"],
        "redirect_uri": f"{redirect_base_url()}/auth/github/callback",
        "scope": "read:user user:email",
        "state": _state_for(request, "github"),
    }
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{urlencode(params)}")


async def github_callback(request: Request, code: str | None, state: str | None) -> RedirectResponse:
    _validate_state(request, "github", state)
    _require_provider("github")
    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code.")

    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": os.environ["GITHUB_CLIENT_ID"],
                "client_secret": os.environ["GITHUB_CLIENT_SECRET"],
                "code": code,
                "redirect_uri": f"{redirect_base_url()}/auth/github/callback",
            },
            headers={"Accept": "application/json"},
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="GitHub did not return an access token.")

        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}
        user_response = await client.get("https://api.github.com/user", headers=headers)
        user_response.raise_for_status()
        github_user = user_response.json()

        email = github_user.get("email")
        if not email:
            email_response = await client.get("https://api.github.com/user/emails", headers=headers)
            if email_response.status_code == 200:
                emails = email_response.json()
                primary = next((item for item in emails if item.get("primary")), None)
                email = (primary or emails[0]).get("email") if emails else None

    return _finish_login(
        request,
        {
            "provider": "github",
            "provider_user_id": str(github_user["id"]),
            "email": email,
            "name": github_user.get("name") or github_user.get("login"),
            "avatar_url": github_user.get("avatar_url"),
        },
    )


def google_login(request: Request) -> RedirectResponse:
    _require_provider("google")
    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": f"{redirect_base_url()}/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": _state_for(request, "google"),
    }
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")


async def google_callback(request: Request, code: str | None, state: str | None) -> RedirectResponse:
    _validate_state(request, "google", state)
    _require_provider("google")
    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code.")

    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{redirect_base_url()}/auth/google/callback",
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Google did not return an access token.")

        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_response.raise_for_status()
        google_user = user_response.json()

    return _finish_login(
        request,
        {
            "provider": "google",
            "provider_user_id": str(google_user["sub"]),
            "email": google_user.get("email"),
            "name": google_user.get("name"),
            "avatar_url": google_user.get("picture"),
        },
    )


def public_current_user(request: Request, user: dict | None) -> dict[str, object]:
    return {"user": public_user(user)}
