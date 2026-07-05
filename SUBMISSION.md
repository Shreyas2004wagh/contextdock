# Where's My Context? - Hackathon Submission

## Track

Best Use of Cognee Cloud

## One-liner

A persistent project-memory assistant for coding agents that should not wake up with yesterday's context missing.

## Problem

LLMs and coding agents are powerful during a session, but they usually restart cold. They forget what files changed, which commands were run, what decisions were made, what broke, and what the next task was.

## Solution

Where's My Context? gives each project a Cognee-backed memory space. The product opens as an Agent Memory OS: sign in with GitHub or Google, run a coding-agent memory case, store session context, improve the graph, recall a handoff brief, and show the Cognee Cloud Receipt without leaving the page.

## Why Cognee Is Core

- `remember()` stores project notes, files, URLs, and coding sessions in a project-scoped Cognee dataset.
- `recall()` answers questions such as "What was I working on yesterday?" and "What should I fix next?"
- `improve()` enriches the selected project memory after a work session.
- `forget()` prunes the selected project memory when a demo or project needs to reset.
- The app shows a lifecycle rail, action trail, source labels, and Cognee Cloud Receipt so Cognee's role is directly visible.

## Demo Flow

1. Open the app and confirm the hero says **Your AI agent remembers every project.**
2. Show the GitHub and Google sign-in options.
3. Sign in, then open the authenticated memory workspace.
4. Click **New Memory Space**.
5. Click **Try Live Memory Case**.
6. Watch it remember an agent session and release context note.
7. Show the action trail entries for `remember()`, `improve()`, and `recall()`.
8. Show the Handoff Brief with decisions, blockers, files, and next action.
9. Click **Copy Memory Receipt** in the Cognee Cloud Receipt.

## What Makes It Different

The demo is not a generic chat app with saved messages. It is a builder-focused memory workflow for agents: session summaries, source labels, project-scoped datasets, lifecycle visibility, and a next-morning recall story that maps directly to real coding work.

## Judging Criteria Fit

- **Potential Impact:** coding agents and LLM tools can resume real project work instead of starting from a blank context window.
- **Creativity & Innovation:** the project turns Codex-style work sessions into persistent project memory, not just chat history.
- **Technical Excellence:** FastAPI and React connect to Cognee lifecycle APIs with project-scoped datasets and local timeline metadata.
- **Best Use of Cognee:** `remember()`, `recall()`, `improve()`, and `forget()` are visible, demoable product actions.
- **User Experience:** the first screen is a product landing page with OAuth CTAs; the real memory workspace appears after sign-in.
- **Presentation Quality:** the README, screenshot, and demo flow all explain the same story: the agent wakes up and Cognee remembers.

## AI Assistant Disclosure

This project was built with help from AI coding assistants, including OpenAI Codex, for planning, implementation, UI iteration, documentation, and validation. The project concept, product direction, testing decisions, and final submission choices were directed by the human participant.

## Final Submission Checklist

- Repository: https://github.com/Shreyas2004wagh/cogneeProject
- Local run: start the FastAPI backend on `127.0.0.1:8000`, then start the Vite frontend on `127.0.0.1:5173`.
- Demo recording: open the app, show GitHub/Google sign-in, sign in, confirm the Cognee Cloud Receipt says `Cognee Cloud`, click **New Memory Space**, click **Try Live Memory Case**, then show the Handoff Brief, lifecycle chips, action trail, and copied memory receipt.
- Safety: rotate the Cognee API key before public submission because it was shared during testing.
- Disclosure: include the AI assistant disclosure above in the submission form.

## Roadmap

- Source-backed answer citations from Cognee recall results when available.
- Git commit import for automatic session memory.
- Project health checks for stale blockers and unresolved next tasks.
- Team-shared memory spaces for multi-agent project handoff.
