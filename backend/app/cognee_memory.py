from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Any

import httpx


def dataset_name(project_id: str) -> str:
    return f"project-{project_id}"


def _cloud_configured() -> bool:
    return bool(os.getenv("COGNEE_API_BASE_URL") and os.getenv("COGNEE_API_KEY"))


def _cloud_headers() -> dict[str, str]:
    headers = {"X-Api-Key": os.environ["COGNEE_API_KEY"]}
    tenant_id = os.getenv("COGNEE_TENANT_ID")
    if tenant_id:
        headers["X-Tenant-Id"] = tenant_id
    return headers


def _cloud_url(path: str) -> str:
    base_url = os.environ["COGNEE_API_BASE_URL"].rstrip("/")
    return f"{base_url}/api/v1/{path.lstrip('/')}"


async def _raise_for_cloud_error(response: httpx.Response) -> None:
    if response.is_success:
        return
    detail: Any
    try:
        detail = response.json()
    except ValueError:
        detail = response.text
    raise RuntimeError(f"Cognee Cloud request failed ({response.status_code}): {detail}")


async def _cloud_remember_bytes(project_id: str, filename: str, data: bytes, content_type: str) -> Any:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            _cloud_url("remember"),
            headers=_cloud_headers(),
            data={"datasetName": dataset_name(project_id), "run_in_background": "false"},
            files=[("data", (filename, data, content_type))],
        )
    await _raise_for_cloud_error(response)
    return response.json()


async def _cloud_recall(project_id: str, query: str) -> Any:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            _cloud_url("recall"),
            headers={**_cloud_headers(), "Content-Type": "application/json"},
            json={
                "searchType": "GRAPH_COMPLETION",
                "datasets": [dataset_name(project_id)],
                "query": query,
                "topK": 10,
                "onlyContext": False,
                "verbose": False,
            },
        )
    await _raise_for_cloud_error(response)
    return response.json()


async def _cloud_improve(project_id: str) -> Any:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            _cloud_url("cognify"),
            headers={**_cloud_headers(), "Content-Type": "application/json"},
            json={"datasets": [dataset_name(project_id)], "run_in_background": False},
        )
    await _raise_for_cloud_error(response)
    return response.json()


async def _cloud_forget(project_id: str) -> Any:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            _cloud_url("forget"),
            headers={**_cloud_headers(), "Content-Type": "application/json"},
            json={"dataset": dataset_name(project_id)},
        )
    await _raise_for_cloud_error(response)
    return response.json()


async def _call_cognee(function_name: str, *args: Any, **kwargs: Any) -> Any:
    import cognee

    fn = getattr(cognee, function_name)
    result = fn(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


async def remember_text(project_id: str, title: str, content: str) -> Any:
    text = f"# {title}\n\n{content.strip()}"
    if _cloud_configured():
        return await _cloud_remember_bytes(project_id, f"{title or 'memory'}.txt", text.encode(), "text/plain")
    return await _call_cognee("remember", text, dataset_name=dataset_name(project_id))


async def remember_url(project_id: str, url: str) -> Any:
    if _cloud_configured():
        return await _cloud_remember_bytes(project_id, "url.txt", url.encode(), "text/plain")
    return await _call_cognee("remember", url, dataset_name=dataset_name(project_id))


async def remember_file(project_id: str, file_path: Path) -> Any:
    if _cloud_configured():
        return await _cloud_remember_bytes(
            project_id,
            file_path.name,
            file_path.read_bytes(),
            "application/octet-stream",
        )
    with file_path.open("rb") as file:
        return await _call_cognee("remember", file, dataset_name=dataset_name(project_id))


def _format_recall_entry(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for key in ("answer", "text", "content", "value", "context"):
            if entry.get(key):
                return str(entry[key])
        return str(entry)
    for attribute in ("answer", "text", "content", "value"):
        value = getattr(entry, attribute, None)
        if value:
            return str(value)
    if hasattr(entry, "model_dump"):
        dumped = entry.model_dump()
        for key in ("answer", "text", "content", "value"):
            if dumped.get(key):
                return str(dumped[key])
        return str(dumped)
    return str(entry)


async def recall(project_id: str, query: str) -> str:
    if _cloud_configured():
        result = await _cloud_recall(project_id, query)
        if isinstance(result, list):
            return "\n\n".join(_format_recall_entry(entry) for entry in result)
        return _format_recall_entry(result)

    result = await _call_cognee("recall", query, datasets=[dataset_name(project_id)])
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        return "\n\n".join(_format_recall_entry(entry) for entry in result)
    return _format_recall_entry(result)


async def improve(project_id: str) -> Any:
    if _cloud_configured():
        return await _cloud_improve(project_id)
    return await _call_cognee("improve", dataset=dataset_name(project_id))


async def forget(project_id: str) -> Any:
    if _cloud_configured():
        return await _cloud_forget(project_id)
    return await _call_cognee("forget", dataset=dataset_name(project_id))
