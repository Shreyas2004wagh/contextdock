# Where's My Context?

A hackathon MVP for agents that should not wake up with amnesia. The app uses Cognee as a permanent graph-vector memory layer so a project assistant can remember notes, files, URLs, decisions, blockers, and next actions across sessions.

## Why this wins the theme

The product makes Cognee's memory lifecycle the core user workflow:

- `remember()` stores project notes, files, and URLs.
- `recall()` answers questions from the selected project memory.
- `improve()` enriches the project's memory graph after a working session.
- `forget()` prunes the selected project dataset.

## App flow

1. Create a project memory space.
2. Paste context from yesterday, upload a file, or ingest a URL.
3. Ask questions like "What should I work on today?"
4. Generate a morning brief from remembered decisions, blockers, and next actions.
5. Improve or forget the selected project memory when needed.

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
```

`.env` is ignored by git. Do not put the API key in frontend code.

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

## 3-day build plan

### Day 1: Working memory loop

- Backend endpoints for `remember`, `recall`, `improve`, and `forget`.
- Project-scoped datasets.
- Frontend controls for notes, URLs, files, recall chat, morning brief, improve, and forget.

### Day 2: Better demo and retrieval

- Add sample project memories and one-click demo seed.
- Add memory timeline and source labels.
- Improve file and URL ingestion UX.
- Tune prompts for morning brief and decision recovery.

### Day 3: Hackathon polish

- Record a short demo: cold start, remember, recall next action, improve, forget.
- Add deployment docs.
- Create submission screenshots.
- Tighten README and pitch.
