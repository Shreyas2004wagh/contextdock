"""Run a real Cloud lifecycle check in an isolated, disposable memory space."""
import os
import tempfile

from dotenv import load_dotenv
from fastapi.testclient import TestClient


def main():
    load_dotenv()
    if not os.getenv("COGNEE_API_BASE_URL") or not os.getenv("COGNEE_API_KEY"):
        raise SystemExit("Cloud credentials are required. No requests sent.")
    with tempfile.TemporaryDirectory(prefix="wmc-smoke-") as directory:
        os.environ.update(APP_DATA_DIR=directory, DATABASE_URL="", APP_ENV="test", RENDER="false", DEV_AUTH_ENABLED="true", ALLOW_GUEST_PROJECTS="false", SESSION_COOKIE_SECURE="false")
        from backend.app.main import app

        def check(label, response):
            print(f"{label}: HTTP {response.status_code}", flush=True)
            if not response.is_success:
                detail = response.json().get("detail", "Request failed.")
                raise RuntimeError(f"{label}: {detail}")
            return response.json()

        remote_created = False
        with TestClient(app) as client:
            client.get("/auth/dev/login", follow_redirects=False)
            project = check("create project", client.post("/projects", json={"name": "Disposable Cloud verification"}))["id"]
            try:
                check("remember note", client.post("/memory/remember/text", json={"project_id": project, "title": "Release note", "content": "Atlas uses three webhook retries. The owner decided to retain idempotency keys for 24 hours."}))
                remote_created = True
                check("remember session", client.post("/memory/remember/session", json={"project_id": project, "summary": "Atlas webhook release handoff", "files_changed": "src/webhooks/delivery.ts", "decisions": "Three retries with exponential backoff.", "blockers": "Timeout-after-success integration test fails.", "next_tasks": "Fix the idempotency check and rerun the webhook suite."}))
                check("remember file", client.post(f"/memory/remember/file?project_id={project}", files={"file": ("checks.txt", b"Webhook validation command: npm run test -- webhooks", "text/plain")}))
                check("remember URL", client.post("/memory/remember/url", json={"project_id": project, "url": "https://example.com"}))
                check("improve", client.post("/memory/improve", json={"project_id": project}))
                answer = check("recall", client.post("/memory/recall", json={"project_id": project, "query": "Summarize the Atlas webhook handoff: files, blocker, decision, and next action."}))["answer"]
                if not answer.strip():
                    raise RuntimeError("Recall returned an empty answer.")
                events = check("timeline", client.get(f"/projects/{project}/events"))
                if not {"remember()", "improve()", "recall()"}.issubset({event["lifecycle"] for event in events}):
                    raise RuntimeError("Timeline is missing a lifecycle event.")
                print("Recall returned non-empty text; lifecycle events verified.", flush=True)
            finally:
                if remote_created:
                    check("forget disposable dataset", client.post("/memory/forget", json={"project_id": project}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit(str(error)) from None
