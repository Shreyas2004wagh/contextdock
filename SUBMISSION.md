# Where's My Context? - Hackathon Submission

## One-liner

A persistent project-memory assistant for coding agents that should not wake up with yesterday's context missing.

## Problem

LLMs and coding agents are powerful during a session, but they usually restart cold. They forget what files changed, which commands were run, what decisions were made, what broke, and what the next task was.

## Solution

Where's My Context? gives each project a Cognee-backed memory space. Users can remember notes, URLs, files, and Codex-style coding session summaries, then ask for a morning brief or targeted recall before starting work again.

## Why Cognee Is Core

- `remember()` stores project notes, files, URLs, and coding sessions in a project-scoped Cognee dataset.
- `recall()` answers questions such as "What was I working on yesterday?" and "What should I fix next?"
- `improve()` enriches the selected project memory after a work session.
- `forget()` prunes the selected project memory when a demo or project needs to reset.
- The app shows a lifecycle rail, Memory Timeline, and Memory Proof panel so judges can see Cognee's role directly.

## Demo Flow

1. Open the app and click **Run Demo**.
2. Watch it remember a Codex-style coding session and project note.
3. Show the Memory Timeline entries for `remember()`, `improve()`, and `recall()`.
4. Ask "What was I working on yesterday?"
5. Click **Morning Brief** to recover decisions, blockers, files that matter, and next actions.

## What Makes It Different

The demo is not a generic chat app with saved messages. It is a builder-focused memory workflow for agents: session summaries, source labels, project-scoped datasets, lifecycle visibility, and a next-morning recall story that maps directly to real coding work.

## Judging Criteria Fit

- **Potential Impact:** coding agents and LLM tools can resume real project work instead of starting from a blank context window.
- **Creativity & Innovation:** the project turns Codex-style work sessions into persistent project memory, not just chat history.
- **Technical Excellence:** FastAPI and React connect to Cognee lifecycle APIs with project-scoped datasets and local timeline metadata.
- **Best Use of Cognee:** `remember()`, `recall()`, `improve()`, and `forget()` are visible, demoable product actions.
- **User Experience:** the first screen is a judge-ready command center with Run Demo, Morning Brief, Memory Proof, and lifecycle activity.
- **Presentation Quality:** the README, screenshot, and demo flow all explain the same story: the agent wakes up and Cognee remembers.

## AI Assistant Disclosure

This project was built with help from AI coding assistants, including OpenAI Codex, for planning, implementation, UI iteration, documentation, and validation. The project concept, product direction, testing decisions, and final submission choices were directed by the human participant.

## Roadmap

- Source-backed answer citations from Cognee recall results when available.
- Git commit import for automatic session memory.
- Project health checks for stale blockers and unresolved next tasks.
- Team-shared memory spaces for multi-agent project handoff.
