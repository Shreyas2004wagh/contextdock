from __future__ import annotations

import json
import re
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
PROJECTS_FILE = DATA_DIR / "projects.json"
EVENTS_FILE = DATA_DIR / "events.json"
USERS_FILE = DATA_DIR / "users.json"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def _load_projects() -> list[dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PROJECTS_FILE.exists():
        return []
    return json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))


def _save_projects(projects: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(projects, indent=2), encoding="utf-8")


def _load_events() -> list[dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not EVENTS_FILE.exists():
        return []
    return json.loads(EVENTS_FILE.read_text(encoding="utf-8"))


def _save_events(events: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")


def _load_users() -> list[dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        return []
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def _save_users(users: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def list_projects(owner_id: str | None = None) -> list[dict[str, Any]]:
    projects = _load_projects()
    if owner_id is None:
        return [project for project in projects if not project.get("owner_id")]
    return [
        project
        for project in projects
        if project.get("owner_id") in {owner_id, None}
    ]


def create_project(name: str, description: str = "", owner_id: str | None = None) -> dict[str, Any]:
    projects = _load_projects()
    base_id = _slugify(name)
    project_id = base_id
    suffix = 2
    existing_ids = {project["id"] for project in projects}
    while project_id in existing_ids:
        project_id = f"{base_id}-{suffix}"
        suffix += 1

    now = datetime.now(timezone.utc).isoformat()
    project = {
        "id": project_id,
        "name": name.strip(),
        "description": description.strip(),
        "owner_id": owner_id,
        "created_at": now,
        "updated_at": now,
    }
    projects.append(project)
    _save_projects(projects)
    log_event(
        project_id,
        "system",
        "project",
        "Project created",
        f"{project['name']} is ready for persistent memory.",
    )
    return project


def touch_project(project_id: str) -> None:
    projects = _load_projects()
    for project in projects:
        if project["id"] == project_id:
            project["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_projects(projects)
            return


def ensure_project(project_id: str, owner_id: str | None = None) -> None:
    for project in _load_projects():
        if project["id"] != project_id:
            continue
        project_owner_id = project.get("owner_id")
        if project_owner_id and owner_id != project_owner_id:
            raise KeyError(project_id)
        return
    raise KeyError(project_id)


def log_event(project_id: str, lifecycle: str, source: str, title: str, detail: str = "") -> dict[str, Any]:
    events = _load_events()
    now = datetime.now(timezone.utc).isoformat()
    event = {
        "id": f"{project_id}-{uuid4().hex[:10]}",
        "project_id": project_id,
        "lifecycle": lifecycle,
        "source": source,
        "title": title,
        "detail": detail,
        "created_at": now,
    }
    events.append(event)
    _save_events(events[-500:])
    return event


def list_project_events(project_id: str, owner_id: str | None = None) -> list[dict[str, Any]]:
    ensure_project(project_id, owner_id)
    events = [event for event in _load_events() if event.get("project_id") == project_id]
    return sorted(events, key=lambda event: event.get("created_at", ""), reverse=True)


def get_user(user_id: str | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    return next((user for user in _load_users() if user["id"] == user_id), None)


def public_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user:
        return None
    return {
        "id": user["id"],
        "provider": user["provider"],
        "email": user.get("email"),
        "name": user.get("name") or user.get("email") or "Signed-in user",
        "avatar_url": user.get("avatar_url"),
    }


def upsert_user(profile: dict[str, Any]) -> dict[str, Any]:
    users = _load_users()
    now = datetime.now(timezone.utc).isoformat()
    existing = next(
        (
            user
            for user in users
            if user["provider"] == profile["provider"]
            and user["provider_user_id"] == profile["provider_user_id"]
        ),
        None,
    )

    if existing:
        existing.update(
            {
                "email": profile.get("email") or existing.get("email"),
                "name": profile.get("name") or existing.get("name"),
                "avatar_url": profile.get("avatar_url") or existing.get("avatar_url"),
                "updated_at": now,
            }
        )
        _save_users(users)
        return existing

    user = {
        "id": uuid4().hex,
        "provider": profile["provider"],
        "provider_user_id": profile["provider_user_id"],
        "email": profile.get("email"),
        "name": profile.get("name"),
        "avatar_url": profile.get("avatar_url"),
        "created_at": now,
        "updated_at": now,
    }
    users.append(user)
    _save_users(users)
    return user
