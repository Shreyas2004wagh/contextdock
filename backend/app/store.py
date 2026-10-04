from __future__ import annotations

import json
import os
from functools import lru_cache
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Column, MetaData, Table, Text, UniqueConstraint, create_engine, select, or_
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

DATA_DIR = Path(os.getenv("APP_DATA_DIR", str(Path(__file__).resolve().parents[1] / "data"))).expanduser().resolve()

schema = MetaData()
metadata = Table("metadata", schema, Column("key", Text, primary_key=True), Column("value", Text, nullable=False))
users = Table("users", schema,
    Column("id", Text, primary_key=True), Column("provider", Text, nullable=False),
    Column("provider_user_id", Text, nullable=False), Column("email", Text), Column("name", Text),
    Column("avatar_url", Text), Column("created_at", Text, nullable=False), Column("updated_at", Text, nullable=False),
    UniqueConstraint("provider", "provider_user_id"))
projects = Table("projects", schema,
    Column("id", Text, primary_key=True), Column("name", Text, nullable=False),
    Column("description", Text, nullable=False, server_default=""), Column("owner_id", Text, index=True),
    Column("created_at", Text, nullable=False), Column("updated_at", Text, nullable=False))
events = Table("events", schema,
    Column("id", Text, primary_key=True), Column("project_id", Text, nullable=False, index=True),
    Column("lifecycle", Text, nullable=False), Column("source", Text, nullable=False),
    Column("title", Text, nullable=False), Column("detail", Text, nullable=False, server_default=""),
    Column("created_at", Text, nullable=False))


def database_url():
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        return make_url(f"sqlite:///{DATA_DIR / 'metadata.sqlite3'}")
    url = make_url(value)
    if url.drivername not in {"postgres", "postgresql", "postgresql+psycopg"}:
        raise ValueError("DATABASE_URL must be a PostgreSQL connection URL.")
    return url.set(drivername="postgresql+psycopg")


def metadata_store() -> str:
    return database_url().get_backend_name()


@lru_cache(maxsize=8)
def _engine(url):
    options = {"connect_args": {"timeout": 30}, "poolclass": NullPool} if url.get_backend_name() == "sqlite" else {
        "connect_args": {"connect_timeout": 15}, "pool_size": 3, "max_overflow": 2}
    return create_engine(url, pool_pre_ping=True, hide_parameters=True, **options)


def _insert(db, table):
    return postgres_insert(table) if db.dialect.name == "postgresql" else sqlite_insert(table)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _db():
    url = database_url()
    if url.get_backend_name() == "sqlite":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _engine(url).begin() as connection:
        # Serialize schema initialization, legacy imports, and writes across workers.
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            connection.exec_driver_sql("SELECT pg_advisory_xact_lock(879341206)")
        schema.create_all(connection)
        if not connection.execute(select(metadata).where(metadata.c.key == "json_migrated")).first():
            for table in (users, projects, events):
                path = DATA_DIR / f"{table.name}.json"
                if not path.exists():
                    continue
                for item in json.loads(path.read_text(encoding="utf-8")):
                    values = {key: item[key] for key in table.c.keys() if key in item}
                    connection.execute(_insert(connection, table).values(**values).on_conflict_do_nothing())
            connection.execute(metadata.insert().values(key="json_migrated", value=_now()))
        yield connection


def initialize_store() -> None:
    with _db():
        pass


def allow_guest_projects() -> bool:
    return os.getenv("ALLOW_GUEST_PROJECTS", "false").lower() == "true"


def list_projects(owner_id: str | None = None) -> list[dict]:
    with _db() as db:
        if not owner_id and not allow_guest_projects():
            return []
        condition = projects.c.owner_id == owner_id
        if allow_guest_projects():
            condition = or_(condition, projects.c.owner_id.is_(None))
        return [dict(row) for row in db.execute(select(projects).where(condition).order_by(projects.c.updated_at.desc())).mappings()]


def create_project(name: str, description: str = "", owner_id: str | None = None) -> dict:
    if not name.strip():
        raise ValueError("A project name is required.")
    if not owner_id and not allow_guest_projects():
        raise PermissionError("Sign in to create a memory space.")
    now = _now()
    project = dict(id=uuid4().hex, name=name.strip(), description=description.strip(), owner_id=owner_id, created_at=now, updated_at=now)
    with _db() as db:
        db.execute(projects.insert().values(**project))
        _insert_event(db, project["id"], "system", "project", "Project created", f"{project['name']} is ready for persistent memory.")
    return project


def touch_project(project_id: str) -> None:
    with _db() as db:
        db.execute(projects.update().where(projects.c.id == project_id).values(updated_at=_now()))


def ensure_project(project_id: str, owner_id: str | None = None) -> None:
    with _db() as db:
        project = db.execute(select(projects.c.owner_id).where(projects.c.id == project_id)).mappings().first()
    if not project:
        raise KeyError(project_id)
    if project["owner_id"] is None:
        if not allow_guest_projects():
            raise KeyError(project_id)
    elif not owner_id or project["owner_id"] != owner_id:
        raise KeyError(project_id)


def _insert_event(db, project_id, lifecycle, source, title, detail):
    event = dict(id=uuid4().hex, project_id=project_id, lifecycle=lifecycle, source=source, title=title, detail=detail, created_at=_now())
    db.execute(events.insert().values(**event))
    return event


def log_event(project_id: str, lifecycle: str, source: str, title: str, detail: str = "") -> dict:
    with _db() as db:
        return _insert_event(db, project_id, lifecycle, source, title, detail)


def clear_project_events(project_id: str) -> None:
    with _db() as db:
        db.execute(events.delete().where(events.c.project_id == project_id))


def list_project_events(project_id: str, owner_id: str | None = None) -> list[dict]:
    ensure_project(project_id, owner_id)
    with _db() as db:
        return [dict(row) for row in db.execute(select(events).where(events.c.project_id == project_id).order_by(events.c.created_at.desc())).mappings()]


def get_user(user_id: str | None) -> dict | None:
    if not user_id:
        return None
    with _db() as db:
        row = db.execute(select(users).where(users.c.id == user_id)).mappings().first()
        return dict(row) if row else None


def public_user(user: dict | None) -> dict | None:
    if not user:
        return None
    return {key: user.get(key) for key in ("id", "provider", "email", "name", "avatar_url")}


def upsert_user(profile: dict) -> dict:
    now = _now()
    with _db() as db:
        existing = db.execute(select(users).where(users.c.provider == profile["provider"], users.c.provider_user_id == profile["provider_user_id"])).mappings().first()
        user = dict(existing) if existing else dict(id=uuid4().hex, created_at=now)
        user.update({key: profile.get(key) or user.get(key) for key in ("provider", "provider_user_id", "email", "name", "avatar_url")})
        user["name"] = user["name"] or user["email"] or "Signed-in user"
        user["updated_at"] = now
        statement = _insert(db, users).values(**user)
        db.execute(statement.on_conflict_do_update(index_elements=[users.c.id],
            set_={key: statement.excluded[key] for key in ("email", "name", "avatar_url", "updated_at")}))
    return user
