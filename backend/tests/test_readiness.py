import asyncio
import json
import os
import socket
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

# Isolate import-time initialization from real metadata and credentials.
_sandbox = tempfile.TemporaryDirectory()
os.environ.update(APP_DATA_DIR=_sandbox.name, DATABASE_URL="", APP_ENV="test", RENDER="false", SESSION_SECRET="test-only-" + "s" * 40, DEV_AUTH_ENABLED="true", ALLOW_GUEST_PROJECTS="false")
from backend.app import auth, cognee_memory, security, store, url_content
from backend.app.main import app


class TemporaryStore:
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.patch = patch.object(store, "DATA_DIR", Path(self.directory.name))
        self.patch.start()
        self.addCleanup(self.patch.stop)


class StoreTests(TemporaryStore, unittest.TestCase):
    def test_database_url_supports_postgres_without_exposing_password(self):
        for scheme in ("postgres", "postgresql", "postgresql+psycopg"):
            with patch.dict(os.environ, {"DATABASE_URL": f"{scheme}://user:private-password@example.com/wmc?sslmode=require"}):
                url = store.database_url()
                self.assertEqual(url.drivername, "postgresql+psycopg")
                self.assertEqual(url.query["sslmode"], "require")
                self.assertNotIn("private-password", str(url))

    def test_json_migration_keeps_ids_answers_and_originals(self):
        folder = Path(self.directory.name)
        now = "2026-01-01T00:00:00Z"
        project = dict(id="legacy-project", name="Legacy", description="", owner_id="owner", created_at=now, updated_at=now)
        event = dict(id="old-event", project_id=project["id"], lifecycle="recall()", source="query", title="Question", detail="x" * 2400, created_at=now)
        (folder / "projects.json").write_text(json.dumps([project]))
        (folder / "events.json").write_text(json.dumps([event]))
        store.initialize_store()
        store.initialize_store()
        self.assertEqual(store.list_projects("owner"), [project])
        self.assertEqual(store.list_project_events(project["id"], "owner"), [event])
        self.assertTrue((folder / "events.json").exists())

    def test_ids_survive_metadata_reset_without_dataset_reuse(self):
        first = store.create_project("Same name", owner_id="owner")
        (Path(self.directory.name) / "metadata.sqlite3").unlink()
        second = store.create_project("Same name", owner_id="owner")
        self.assertNotEqual(first["id"], second["id"])

    def test_concurrent_writes_are_retained(self):
        project = store.create_project("Parallel", owner_id="owner")
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda index: store.log_event(project["id"], "remember()", "note", str(index)), range(40)))
        self.assertEqual(len(store.list_project_events(project["id"], "owner")), 41)

    def test_private_projects_and_explicit_guest_policy(self):
        project = store.create_project("Private", owner_id="alice")
        self.assertEqual(store.list_projects("bob"), [])
        self.assertEqual(store.list_projects(), [])
        with self.assertRaises(KeyError):
            store.ensure_project(project["id"], "bob")
        with self.assertRaises(PermissionError):
            store.create_project("Anonymous")

    def test_events_are_not_globally_truncated(self):
        project = store.create_project("Long history", owner_id="owner")
        for index in range(505):
            store.log_event(project["id"], "remember()", "note", str(index))
        self.assertEqual(len(store.list_project_events(project["id"], "owner")), 506)


class APITests(TemporaryStore, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        middleware = app.middleware_stack
        while middleware:
            if isinstance(middleware, security.RequestLimitsMiddleware):
                middleware.windows.clear()
            middleware = getattr(middleware, "app", None)

    def signed_in_project(self):
        response = self.client.get("/auth/dev/login", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        response = self.client.post("/projects", json={"name": "Test space"})
        self.assertEqual(response.status_code, 200)
        return response.json()["id"]

    def test_signin_required_and_foreign_origin_rejected(self):
        self.assertEqual(self.client.post("/projects", json={"name": "No auth"}).status_code, 401)
        project = self.signed_in_project()
        self.assertEqual(self.client.post("/memory/forget", json={"project_id": project}, headers={"Origin": "https://evil.example"}).status_code, 403)

    def test_other_users_cannot_read_or_delete_private_memory(self):
        self.signed_in_project()
        other = store.create_project("Other owner", owner_id="someone-else")
        with patch.object(cognee_memory, "forget", new_callable=AsyncMock) as forget:
            self.assertEqual(self.client.get(f"/projects/{other['id']}/events").status_code, 404)
            self.assertEqual(self.client.post("/memory/forget", json={"project_id": other["id"]}).status_code, 404)
            forget.assert_not_awaited()

    def test_full_recall_survives_reload_and_forget_clears_content(self):
        project = self.signed_in_project()
        answer = "A complete answer. " * 200
        with patch.object(cognee_memory, "recall", new_callable=AsyncMock, return_value=answer):
            result = self.client.post("/memory/recall", json={"project_id": project, "query": "What next?"})
        self.assertEqual(result.json()["answer"], answer)
        events = self.client.get(f"/projects/{project}/events").json()
        self.assertEqual(events[0]["detail"], answer)
        with patch.object(cognee_memory, "forget", new_callable=AsyncMock):
            self.assertEqual(self.client.post("/memory/forget", json={"project_id": project}).status_code, 200)
        events = self.client.get(f"/projects/{project}/events").json()
        self.assertEqual([event["lifecycle"] for event in events], ["forget()"])

    def test_forget_failure_preserves_history_and_redacts_upstream_error(self):
        project = self.signed_in_project()
        before = self.client.get(f"/projects/{project}/events").json()
        with patch.object(cognee_memory, "forget", new_callable=AsyncMock, side_effect=RuntimeError("secret-should-not-appear")):
            result = self.client.post("/memory/forget", json={"project_id": project})
        self.assertEqual(result.status_code, 502)
        self.assertNotIn("secret-should-not-appear", result.text)
        self.assertEqual(self.client.get(f"/projects/{project}/events").json(), before)

    def test_input_validation_and_upload_limits(self):
        project = self.signed_in_project()
        self.assertEqual(self.client.post("/projects", json={"name": "  "}).status_code, 422)
        route = f"/memory/remember/file?project_id={project}"
        with patch.object(cognee_memory, "remember_file", new_callable=AsyncMock) as remember:
            self.assertEqual(self.client.post(route, files={"file": ("a.exe", b"bad")}).status_code, 415)
            self.assertEqual(self.client.post(route, files={"file": ("a.txt", b"")}).status_code, 422)
            self.assertEqual(self.client.post(route, files={"file": ("a.txt", b"x" * (security.MAX_UPLOAD_BYTES + 1))}).status_code, 413)
            remember.assert_not_awaited()
            self.assertEqual(self.client.post(route, files={"file": ("a.txt", b"hello")}).status_code, 200)
            remember.assert_awaited_once()

    def test_body_limit_without_trusting_content_length(self):
        self.signed_in_project()
        body = iter([b"x" * (security.MAX_REQUEST_BYTES // 2), b"x" * (security.MAX_REQUEST_BYTES // 2 + 1)])
        response = self.client.post("/projects", content=body, headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 413)

    def test_rate_limit(self):
        statuses = [self.client.post("/projects", json={"name": "Anonymous"}).status_code for _ in range(31)]
        self.assertEqual(statuses[-1], 429)

    def test_oauth_missing_state(self):
        self.assertEqual(self.client.get("/auth/github/callback").status_code, 400)

    def test_oauth_callbacks_persist_identity_and_logout(self):
        for provider in ("github", "google"):
            with self.subTest(provider=provider), patch.dict(os.environ, {
                f"{provider.upper()}_CLIENT_ID": "test-client",
                f"{provider.upper()}_CLIENT_SECRET": "test-secret",
            }):
                redirect = self.client.get(f"/auth/{provider}/login", follow_redirects=False)
                state = parse_qs(urlparse(redirect.headers["location"]).query)["state"][0]
                profile = {"id": 123, "sub": "google-user", "name": "Test User", "email": "test@example.com"}
                def reply(body):
                    return httpx.Response(200, json=body, request=httpx.Request("GET", "https://provider.example"))
                with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=reply({"access_token": "private-test-token"})), patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=reply(profile)):
                    result = self.client.get(f"/auth/{provider}/callback", params={"state": state, "code": "test-code"}, follow_redirects=False)
                self.assertEqual(result.status_code, 307)
                me = self.client.get("/auth/me").json()["user"]
                self.assertEqual(me["provider"], provider)
                project = self.client.post("/projects", json={"name": "OAuth space"}).json()
                self.assertEqual(project["owner_id"], me["id"])
                self.assertNotIn("private-test-token", result.headers.get("set-cookie", ""))
                self.assertEqual(self.client.get(f"/auth/{provider}/callback", params={"state": state, "code": "test-code"}).status_code, 400)
                self.assertEqual(self.client.post("/auth/logout").status_code, 200)
                self.assertIsNone(self.client.get("/auth/me").json()["user"])
                self.assertEqual(self.client.get("/projects").json(), [])

    def test_oauth_provider_failure_is_safe_and_does_not_sign_in(self):
        with patch.dict(os.environ, {"GITHUB_CLIENT_ID": "test-client", "GITHUB_CLIENT_SECRET": "test-secret"}):
            redirect = self.client.get("/auth/github/login", follow_redirects=False)
            state = parse_qs(urlparse(redirect.headers["location"]).query)["state"][0]
            with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, side_effect=httpx.ConnectError("private-provider-details")):
                response = self.client.get("/auth/github/callback", params={"state": state, "code": "test-code"})
            self.assertEqual(response.status_code, 502)
            self.assertNotIn("private-provider-details", response.text)
            self.assertIsNone(self.client.get("/auth/me").json()["user"])


class SecurityTests(unittest.TestCase):
    def test_oauth_state_expires_and_is_single_use(self):
        request = Request({"type": "http", "session": {"oauth_state": "valid", "oauth_provider": "github", "oauth_issued_at": time.time()}})
        auth._validate_state(request, "github", "valid")
        with self.assertRaises(HTTPException):
            auth._validate_state(request, "github", "valid")
        request.session.update(oauth_state="old", oauth_provider="github", oauth_issued_at=time.time() - 700)
        with self.assertRaises(HTTPException):
            auth._validate_state(request, "github", "old")

    def test_production_rejects_unsafe_config(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "SESSION_SECRET": "dev-session-secret-change-me"}):
            with self.assertRaises(RuntimeError):
                security.session_secret()
        with patch.dict(os.environ, {"APP_ENV": "production", "SESSION_COOKIE_SECURE": "true", "DEV_AUTH_ENABLED": "true"}):
            with self.assertRaises(RuntimeError):
                security.session_secret()

    def test_production_requires_external_database(self):
        settings = {"APP_ENV": "production", "SESSION_COOKIE_SECURE": "true", "DEV_AUTH_ENABLED": "false", "DATABASE_URL": ""}
        with patch.dict(os.environ, settings):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL"):
                security.session_secret()
        settings["DATABASE_URL"] = "postgresql://user:password@example.com/wmc"
        with patch.dict(os.environ, settings):
            self.assertEqual(security.session_secret(), os.environ["SESSION_SECRET"])


class URLTests(unittest.IsolatedAsyncioTestCase):
    async def test_private_ips_and_credentials_are_rejected(self):
        for url in ("http://127.0.0.1", "http://[::1]", "http://169.254.169.254", "file:///etc/passwd", "https://user:pass@example.com", "http://example.com:8000"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                await url_content.resolve_public_url(url)

    async def test_public_host_resolving_to_private_address_is_rejected(self):
        addresses = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))]
        with patch("socket.getaddrinfo", return_value=addresses), self.assertRaises(ValueError):
            await url_content.resolve_public_url("https://public-looking.example")

    async def test_url_content_is_extracted_and_dns_is_pinned(self):
        addresses = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
        response = httpx.Response(200, headers={"Content-Type": "text/html"}, stream=httpx.ByteStream(b"<h1>Release notes</h1><script>ignore me</script><p>Retry three times.</p>"))
        with patch("socket.getaddrinfo", return_value=addresses), patch.object(httpx.AsyncClient, "send", new_callable=AsyncMock, return_value=response) as send:
            text = await url_content.fetch_url_text("https://example.com/notes")
            sent = send.call_args.args[0]
        self.assertIn("Release notes", text)
        self.assertNotIn("ignore me", text)
        self.assertEqual(sent.url.host, "93.184.216.34")
        self.assertEqual(sent.extensions["sni_hostname"], "example.com")
        self.assertEqual(sent.headers["host"], "example.com")

    async def test_redirect_target_is_revalidated(self):
        response = httpx.Response(302, headers={"Location": "http://127.0.0.1/private"})
        original = url_content.resolve_public_url

        async def resolver(url):
            if url == "https://example.com":
                return httpx.URL(url), "93.184.216.34"
            return await original(url)

        with patch.object(url_content, "resolve_public_url", side_effect=resolver), patch.object(httpx.AsyncClient, "send", new_callable=AsyncMock, return_value=response), self.assertRaises(ValueError):
            await url_content.fetch_url_text("https://example.com")

    async def test_cloud_improve_targets_enrichment_not_cognify(self):
        response = httpx.Response(200, json={"status": "ok"})
        with patch.dict(os.environ, {"COGNEE_API_BASE_URL": "https://memory.example", "COGNEE_API_KEY": "test-key"}), patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=response) as post:
            await cognee_memory._cloud_improve("sample")
        self.assertTrue(post.call_args.args[0].endswith("/api/v1/improve"))
        self.assertEqual(post.call_args.kwargs["json"]["datasetName"], "project-sample")

    async def test_upstream_error_does_not_include_response_body(self):
        with self.assertRaises(cognee_memory.CloudMemoryError) as result:
            await cognee_memory._raise_for_cloud_error(httpx.Response(429, text="private upstream details"))
        self.assertNotIn("private", str(result.exception))


if __name__ == "__main__":
    unittest.main()
