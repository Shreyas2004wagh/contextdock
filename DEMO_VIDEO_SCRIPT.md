# Where's My Context? 3-Minute Demo Script

Use this while recording screen only. Keep the browser zoom around 90-100%.

## 0:00-0:20 - About The Project

Screen: Open the deployed frontend or local app landing page.

Cursor: Point at the headline **Your AI agent remembers every project.**

Say:
“This is Where’s My Context, an Agent Memory OS for coding agents. The problem is that AI agents usually wake up with no memory of the previous coding session. They forget files, decisions, blockers, commands, and next actions. This project gives each agent a persistent project memory powered by Cognee Cloud.”

Cursor: Point at **Start with GitHub**, **Continue with Google**, and **Open Workspace**.

Say:
“The product starts like a real workspace: users sign in first, then their private memory space opens.”

## 0:20-0:45 - Product Flow

Cursor: Point at the right preview card **Sign in to unlock the workspace**.

Say:
“After sign-in, the user unlocks project memory spaces, handoff briefs, source labels, lifecycle proof, and builder controls.”

Cursor: Point across the stage rail:
**Trigger → remember() → improve() → recall() → Handoff Brief**

Say:
“This rail shows the Cognee memory lifecycle directly inside the product: remember, improve, recall, and then produce a handoff brief.”

## 0:45-1:05 - Sign In

Screen: Click **Continue as Demo User** for local recording.

Cursor: Point at the signed-in profile chip in the navbar.

Say:
“For this recording I’m using a local demo sign-in. In production, the same flow is handled through real GitHub or Google OAuth. Once signed in, the actual workspace becomes available.”

## 1:05-1:35 - Run The Live Memory Case

Screen: Click **New Memory Space**.

Say:
“First I create a memory space for a project. You can think of this as a persistent brain for one codebase or release.”

Screen: Click **Try Live Memory Case**.

Cursor: Keep cursor near the stage rail/action area while it runs.

Say:
“Now I run the live memory case. The app remembers an agent session, stores release handoff context, improves the memory graph, and asks Cognee to recall useful project context.”

Cursor: Point at lifecycle/action trail entries as they appear.

Say:
“These are real backend calls into the Cognee lifecycle, not just static UI: remember, improve, and recall.”

## 1:35-2:05 - Demo Result

Cursor: Point at **Handoff Brief / Recovered context**.

Say:
“This is the main result. The agent gets a handoff brief with decisions, blockers, important files, and the next action. So instead of re-explaining the project to the AI, the agent starts with remembered context.”

Cursor: Point at **Cognee Cloud Receipt**.

Say:
“The receipt shows the memory provider, dataset, remembered sources, and latest lifecycle call. It makes the Cognee usage visible and trustworthy.”

## 2:05-2:30 - Tech Stack And Architecture

Cursor: Scroll to or point at **Architecture** if visible.

Say:
“The frontend is React and Vite. The backend is FastAPI. Authentication uses GitHub and Google OAuth with session cookies. Cognee Cloud is the persistent memory layer, and local JSON is only used for project metadata and timeline events. The app is deployed with Vercel for the frontend and Render for the backend.”

## 2:30-2:50 - Builder Controls

Cursor: Scroll to **Builder Controls**.

Say:
“Users can also build memory manually by adding session summaries, files changed, commands run, decisions, blockers, notes, URLs, and file uploads. These become project memory that Cognee can recall later.”

## 2:50-3:00 - Closing

Cursor: Return to the Handoff Brief or Cognee Cloud Receipt.

Say:
“The biggest learning was how to turn memory from a hidden backend feature into a visible product workflow. Where’s My Context uses Cognee so coding agents do not wake up cold. They remember the project and continue from where work actually stopped.”

