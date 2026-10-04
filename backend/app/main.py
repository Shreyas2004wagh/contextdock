from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

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
from . import auth  # noqa: E402
from .models import (
    ForgetRequest,
    ImproveRequest,
    ProjectCreate,
    RecallRequest,
    RememberSessionRequest,
    RememberTextRequest,
    RememberUrlRequest,
)
from .store import clear_project_events, create_project, ensure_project, get_user, initialize_store, list_project_events, list_projects, log_event, touch_project, metadata_store
from .security import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_BYTES, RequestLimitsMiddleware, session_secret


@asynccontextmanager
async def lifespan(app):
    initialize_store()
    yield


app = FastAPI(title="ContextDock API", lifespan=lifespan)


def memory_error(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, cognee_memory.CloudMemoryError):
        if exc.status_code == 429:
            return HTTPException(status_code=503, detail="Cognee Cloud is rate-limited. Try again later.", headers={"Retry-After": "60"})
        if exc.status_code in {401, 403}:
            return HTTPException(status_code=503, detail="Cognee Cloud rejected the configured credentials.")
    return HTTPException(status_code=502, detail="The memory service could not complete this request. Please try again later.")

frontend_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://cognee-project.vercel.app",
    auth.frontend_url(),
]
extra_frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(RequestLimitsMiddleware, allowed_origins=[*frontend_origins, *extra_frontend_origins])
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret(),
    same_site=os.getenv("SESSION_COOKIE_SAMESITE", "lax"),
    https_only=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    max_age=7 * 24 * 60 * 60,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[*frontend_origins, *extra_frontend_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    memory_mode = "cloud" if os.getenv("COGNEE_API_BASE_URL") and os.getenv("COGNEE_API_KEY") else "local"
    return {"status": "ok", "memory_mode": memory_mode, "memory_connectivity": "not_checked", "metadata_store": metadata_store()}


@app.get("/auth/providers")
async def auth_providers() -> dict:
    return auth.auth_providers()


@app.get("/auth/github/login")
async def auth_github_login(request: Request):
    return auth.github_login(request)


@app.get("/auth/github/callback")
async def auth_github_callback(request: Request, code: str | None = None, state: str | None = None):
    return await auth.complete_callback("github", request, code, state)


@app.get("/auth/google/login")
async def auth_google_login(request: Request):
    return auth.google_login(request)


@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, code: str | None = None, state: str | None = None):
    return await auth.complete_callback("google", request, code, state)


@app.get("/auth/dev/login")
async def auth_dev_login(request: Request):
    return auth.dev_login(request)


@app.get("/auth/me")
async def auth_me(request: Request) -> dict:
    return auth.public_current_user(request, get_user(auth.current_user_id(request)))


@app.post("/auth/logout")
async def auth_logout(request: Request) -> dict:
    auth.clear_session(request)
    return {"status": "logged_out"}


@app.get("/projects")
async def projects(request: Request) -> list[dict]:
    return list_projects(auth.current_user_id(request))


@app.get("/projects/{project_id}/events", dependencies=[Depends(auth.require_access)])
async def project_events(request: Request, project_id: str) -> list[dict]:
    try:
        return list_project_events(project_id, auth.current_user_id(request))
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None


@app.post("/projects", dependencies=[Depends(auth.require_access)])
async def add_project(request: Request, payload: ProjectCreate) -> dict:
    return create_project(payload.name, payload.description, auth.current_user_id(request))


@app.post("/memory/remember/text", dependencies=[Depends(auth.require_access)])
async def remember_text(request: Request, payload: RememberTextRequest) -> dict:
    try:
        ensure_project(payload.project_id, auth.current_user_id(request))
        await cognee_memory.remember_text(payload.project_id, payload.title, payload.content)
        touch_project(payload.project_id)
        log_event(payload.project_id, "remember()", "note", payload.title, payload.content[:280])
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise memory_error(exc) from exc
    return {"status": "remembered"}


@app.post("/memory/remember/url", dependencies=[Depends(auth.require_access)])
async def remember_url(request: Request, payload: RememberUrlRequest) -> dict:
    try:
        ensure_project(payload.project_id, auth.current_user_id(request))
        await cognee_memory.remember_url(payload.project_id, payload.url)
        touch_project(payload.project_id)
        log_event(payload.project_id, "remember()", "url", "URL ingested", payload.url)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise memory_error(exc) from exc
    return {"status": "remembered"}


@app.post("/memory/remember/file", dependencies=[Depends(auth.require_access)])
async def remember_file(request: Request, project_id: str, file: UploadFile = File(...)) -> dict:
    try:
        ensure_project(project_id, auth.current_user_id(request))
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None

    suffix = Path(file.filename or "upload.txt").suffix
    if suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
        await file.close()
        raise HTTPException(status_code=415, detail="Unsupported file type. Upload text, code, PDF, or DOCX files.")
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = Path(temp_file.name)
            size = 0
            while chunk := await file.read(64 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Files must be 10 MB or smaller.")
                temp_file.write(chunk)
            if size == 0:
                raise HTTPException(status_code=422, detail="The uploaded file is empty.")
        await cognee_memory.remember_file(project_id, temp_path)
        touch_project(project_id)
        log_event(project_id, "remember()", "file", "File uploaded", file.filename or "uploaded file")
    except HTTPException:
        raise
    except Exception as exc:
        raise memory_error(exc) from exc
    finally:
        await file.close()
        if "temp_path" in locals() and temp_path.exists():
            temp_path.unlink(missing_ok=True)
    return {"status": "remembered"}


def _format_session_memory(payload: RememberSessionRequest) -> str:
    sections = [
        ("Session summary", payload.summary),
        ("Files changed", payload.files_changed),
        ("Commands run", payload.commands_run),
        ("Decisions made", payload.decisions),
        ("Blockers", payload.blockers),
        ("Next tasks", payload.next_tasks),
    ]
    lines = ["# Codex coding session memory", ""]
    for heading, value in sections:
        clean_value = value.strip() or "None captured."
        lines.extend([f"## {heading}", clean_value, ""])
    return "\n".join(lines).strip()


@app.post("/memory/remember/session", dependencies=[Depends(auth.require_access)])
async def remember_session(request: Request, payload: RememberSessionRequest) -> dict:
    try:
        ensure_project(payload.project_id, auth.current_user_id(request))
        session_memory = _format_session_memory(payload)
        await cognee_memory.remember_text(payload.project_id, "Codex coding session", session_memory)
        touch_project(payload.project_id)
        log_event(payload.project_id, "remember()", "session", "Codex session remembered", payload.summary[:280])
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise memory_error(exc) from exc
    return {"status": "remembered"}


@app.post("/memory/recall", dependencies=[Depends(auth.require_access)])
async def recall(request: Request, payload: RecallRequest) -> dict:
    try:
        ensure_project(payload.project_id, auth.current_user_id(request))
        answer = await cognee_memory.recall(payload.project_id, payload.query)
        log_event(payload.project_id, "recall()", "query", payload.query, answer)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise memory_error(exc) from exc
    return {"answer": answer}


@app.post("/memory/improve", dependencies=[Depends(auth.require_access)])
async def improve(request: Request, payload: ImproveRequest) -> dict:
    try:
        ensure_project(payload.project_id, auth.current_user_id(request))
        await cognee_memory.improve(payload.project_id)
        touch_project(payload.project_id)
        log_event(payload.project_id, "improve()", "system", "Memory graph improved", "Cognee enriched this project memory.")
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise memory_error(exc) from exc
    return {"status": "improved"}


@app.post("/memory/forget", dependencies=[Depends(auth.require_access)])
async def forget(request: Request, payload: ForgetRequest) -> dict:
    try:
        ensure_project(payload.project_id, auth.current_user_id(request))
        await cognee_memory.forget(payload.project_id)
        clear_project_events(payload.project_id)
        touch_project(payload.project_id)
        log_event(payload.project_id, "forget()", "system", "Dataset forgotten", "Cognee pruned the selected project dataset.")
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    except Exception as exc:
        raise memory_error(exc) from exc
    return {"status": "forgotten"}
