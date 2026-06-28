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


def list_projects() -> list[dict[str, Any]]:
    return _load_projects()


def create_project(name: str, description: str = "") -> dict[str, Any]:
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


def ensure_project(project_id: str) -> None:
    if not any(project["id"] == project_id for project in _load_projects()):
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


def list_project_events(project_id: str) -> list[dict[str, Any]]:
    ensure_project(project_id)
    events = [event for event in _load_events() if event.get("project_id") == project_id]
    return sorted(events, key=lambda event: event.get("created_at", ""), reverse=True)
