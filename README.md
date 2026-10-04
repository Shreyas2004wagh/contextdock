# ContextDock

An Agent Memory OS for coding agents that should not wake up with amnesia. The app uses Cognee as a permanent graph-vector memory layer so a project assistant can remember notes, files, URLs, decisions, blockers, and next actions across sessions.

**Hackathon track:** Best Use of Cognee Cloud.

## Why this wins the theme

The product makes Cognee's memory lifecycle the core user workflow:

- `remember()` stores project notes, files, and URLs.
- `recall()` answers questions from the selected project memory.
- `improve()` enriches the project's memory graph after a working session.
- `forget()` prunes the selected project dataset.

## Submission pitch

Agents and LLM tools wake up stateless. **ContextDock** gives them a persistent project brain, so a coding agent can remember yesterday's files, commands, decisions, blockers, and next tasks before starting the next session.

Cognee is central because the app does not just save local notes:

- every project gets a Cognee-scoped dataset;
- every note, URL, file, and Codex-style session enters Cognee through `remember()`;
- answers and morning briefs come back through Cognee `recall()`;
- the timeline makes the memory lifecycle visible for judges.

## Demo-ready features

- Real GitHub and Google OAuth sign-in before the workspace opens.
- Landing-first product flow with the real memory workspace shown after sign-in.
- Codex-style coding session memory for files changed, commands run, decisions, blockers, and next tasks.
- Memory timeline that shows the Cognee lifecycle calls made for the selected project.
- Source labels for remembered notes, URLs, files, coding sessions, and recall answers.
- Handoff brief recall that asks Cognee for decisions, blockers, files that matter, and next actions.
- Cognee Cloud Receipt showing provider mode, dataset name, remembered source count, latest lifecycle call, source labels, and copyable memory receipt.
- Product-story homepage focused on the winning moment: an AI agent remembers every project.
- Architecture and "how it works" sections that explain React/Vite, FastAPI, Cognee Cloud, database-backed timeline metadata, Vercel, and Render.

## Judging criteria fit

- **Potential Impact:** agents resume project work with remembered files, decisions, blockers, and next tasks.
- **Creativity & Innovation:** Codex-style coding sessions become persistent memory, not throwaway chat logs.
- **Technical Excellence:** FastAPI + React expose project-scoped Cognee lifecycle workflows.
- **Best Use of Cognee:** `remember()`, `recall()`, `improve()`, and `forget()` are all visible product actions.
- **User Experience:** OAuth CTAs and product story appear first; after sign-in, Run memory case, Handoff Brief, Cognee Cloud Receipt, lifecycle activity, and timeline appear before editing forms.
- **Presentation Quality:** the app, README, screenshot, and submission notes tell the same memory story.

## Screenshot

![ContextDock workspace preview (previous branding)](frontend/public/workspace-preview.png)

## Cognee lifecycle mapping

| Product action | Cognee lifecycle | Backend route |
| --- | --- | --- |
| Remember note, URL, file, or session | `remember()` | `/memory/remember/*` |
| Ask a question or handoff brief | `recall()` | `/memory/recall` |
| Enrich project memory after work | `improve()` / memify | `/memory/improve` |
| Prune selected project memory | `forget()` | `/memory/forget` |
| Sign in with GitHub or Google | app auth | `/auth/*` |

## App flow

1. Sign in with a configured GitHub or Google provider.
2. Create a project memory space.
3. Open the authenticated workspace.
4. Click **Run memory case** to store an agent session, remember a note, improve the graph, and recall product prompts.
5. Show the Handoff Brief artifact and Cognee Cloud Receipt.
6. Ask questions like "What changed in the last agent session?" or "Which files matter?"
7. Use the builder controls to paste context, upload a file, ingest a URL, or remember a custom coding session.
8. Improve or forget the selected project memory when needed.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

Fill `.env` with Cognee Platform variables:

```powershell
COGNEE_API_BASE_URL=https://tenant-xxxx.aws.cognee.ai
COGNEE_API_KEY=your-platform-key
COGNEE_TENANT_ID=your-tenant-id
SESSION_SECRET=generate-a-long-random-secret
FRONTEND_URL=http://127.0.0.1:5173
OAUTH_REDIRECT_BASE_URL=http://127.0.0.1:8000
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

`.env` is ignored by git. Do not put the API key in frontend code.

For Vercel + Render, set `FRONTEND_URL=https://cognee-project.vercel.app`, `OAUTH_REDIRECT_BASE_URL=https://cogneeproject.onrender.com`, `SESSION_COOKIE_SAMESITE=none`, and `SESSION_COOKIE_SECURE=true`.

If an API key was ever shared in chat, screenshots, or a recording, rotate it before submitting publicly.

Install frontend dependencies:

```powershell
cd frontend
npm install
```

## Run

Backend:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Production Readiness

Use a dedicated external PostgreSQL database for metadata on free Render hosting.
Set `DATABASE_URL` to its connection URL (with the provider's required TLS settings).
Do not use an unrelated application's database. Cognee remains the memory layer;
PostgreSQL holds users, project ownership, and lifecycle history, including recall answers.
Without `DATABASE_URL`, local development uses `backend/data/metadata.sqlite3`.
Legacy JSON in that directory is imported once, retaining IDs and original files.
Back up existing metadata before deploying; local files do not survive a free Render redeploy.
An existing SQLite database is not automatically copied to PostgreSQL.

Required Render configuration:

```dotenv
APP_ENV=production
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DEDICATED_DATABASE?sslmode=require
SESSION_SECRET=<random secret of at least 32 characters>
DEV_AUTH_ENABLED=false
ALLOW_GUEST_PROJECTS=false
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=none
FRONTEND_URL=https://cognee-project.vercel.app
OAUTH_REDIRECT_BASE_URL=https://cogneeproject.onrender.com
```

Also configure Cognee credentials and at least one OAuth provider in Render.
GitHub's callback is `/auth/github/callback`; Google's is `/auth/google/callback`,
both on the backend origin. Set Vercel's `VITE_API_BASE` to the backend origin.
Cross-site authentication requires third-party cookies; browsers blocking them need
a same-site domain or proxy deployment. Disabled OAuth buttons mean credentials are missing.

Uploads are limited to 10 MB and supported document/code extensions. URL ingestion
fetches public HTML/plain text/Markdown with DNS and redirect validation, a 1 MB
response limit, and no script execution. Private network URLs are rejected.
Writes are limited to 30 requests per minute per user/IP per backend process.
Forgetting requires confirmation and clears local history only after Cognee succeeds.
Ownerless legacy projects are hidden by default; do not enable guest access in production.

`/health` reports configuration, not a live Cognee connectivity guarantee.
Cloud errors and rate limits are surfaced without exposing upstream response bodies.

```sh
python -m unittest discover -s backend/tests -v
python -m compileall backend
cd frontend
npm run build
```

With Cloud credentials configured, `python -m backend.scripts.smoke_cloud` runs
an isolated live lifecycle test and attempts to forget its disposable dataset afterward.
It does not use your configured production metadata database. Live Cloud validation
must pass before claiming production readiness; a rate-limited request is not a pass.

## Submission notes

- Rotate any exposed Cognee API key before submitting publicly.
- The app declares AI assistant usage in `SUBMISSION.md`, as required by the hackathon rules.
- Use the screenshot, Cognee Cloud Receipt, and `SUBMISSION.md` summary for the submission page.
