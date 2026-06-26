from __future__ import annotations

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")

ROOT_DIR = Path(__file__).resolve().parents[2]


def _absolute_env_path(name: str, fallback: str) -> None:
    value = os.environ.get(name, fallback)
    path = Path(value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    os.environ[name] = str(path)


_absolute_env_path("DATA_ROOT_DIRECTORY", "backend/data/cognee/data")
_absolute_env_path("SYSTEM_ROOT_DIRECTORY", "backend/data/cognee/system")
_absolute_env_path("CACHE_ROOT_DIRECTORY", "backend/data/cognee/cache")
_absolute_env_path("COGNEE_LOGS_DIR", "backend/data/cognee/logs")

from . import cognee_memory  # noqa: E402
from .models import (
    ForgetRequest,
    ImproveRequest,
    ProjectCreate,
    RecallRequest,
    RememberTextRequest,
    RememberUrlRequest,
)
from .store import create_project, ensure_project, list_projects, touch_project


app = FastAPI(title="Where's My Context API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/projects")
async def projects() -> list[dict]:
    return list_projects()


@app.post("/projects")
async def add_project(payload: ProjectCreate) -> dict:
    return create_project(payload.name, payload.description)


@app.post("/memory/remember/text")
async def remember_text(payload: RememberTextRequest) -> dict:
    try:
        ensure_project(payload.project_id)
        await cognee_memory.remember_text(payload.project_id, payload.title, payload.content)
        touch_project(payload.project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "remembered"}


@app.post("/memory/remember/url")
async def remember_url(payload: RememberUrlRequest) -> dict:
    try:
        ensure_project(payload.project_id)
        await cognee_memory.remember_url(payload.project_id, payload.url)
        touch_project(payload.project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "remembered"}


@app.post("/memory/remember/file")
async def remember_file(project_id: str, file: UploadFile = File(...)) -> dict:
    try:
        ensure_project(project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None

    suffix = Path(file.filename or "upload.txt").suffix
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(await file.read())
        await cognee_memory.remember_file(project_id, temp_path)
        touch_project(project_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if "temp_path" in locals() and temp_path.exists():
            temp_path.unlink(missing_ok=True)
    return {"status": "remembered"}


@app.post("/memory/recall")
async def recall(payload: RecallRequest) -> dict:
    try:
        ensure_project(payload.project_id)
        answer = await cognee_memory.recall(payload.project_id, payload.query)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"answer": answer}


@app.post("/memory/improve")
async def improve(payload: ImproveRequest) -> dict:
    try:
        ensure_project(payload.project_id)
        await cognee_memory.improve(payload.project_id)
        touch_project(payload.project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "improved"}


@app.post("/memory/forget")
async def forget(payload: ForgetRequest) -> dict:
    try:
        ensure_project(payload.project_id)
        await cognee_memory.forget(payload.project_id)
        touch_project(payload.project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "forgotten"}
