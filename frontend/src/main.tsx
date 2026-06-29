import { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Brain,
  Clock3,
  Code2,
  FileUp,
  Lightbulb,
  Link,
  ListChecks,
  MessageSquareText,
  Play,
  RefreshCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  Health,
  MemoryEvent,
  Project,
  SessionMemory,
  createProject,
  forget,
  getHealth,
  getProjectEvents,
  getProjects,
  improve,
  recall,
  rememberFile,
  rememberSession,
  rememberText,
  rememberUrl,
} from "./api";
import "./styles.css";

type FeedItem = {
  kind: "memory" | "answer" | "system";
  source: string;
  title: string;
  body: string;
  related?: string;
};

const demoMemory = `Doug is the groom. The wedding is Sunday.
We chose FastAPI because Cognee is Python-native and lets us ship memory endpoints quickly.
Yesterday's blocker: file ingestion failed for large PDFs.
Next action: fix upload validation, then generate the morning context brief.`;

const demoSession: SessionMemory = {
  summary:
    "Built the MVP for Where's My Context, a Cognee-backed project memory assistant for agents that should not wake up cold.",
  files_changed: "backend/app/main.py, backend/app/cognee_memory.py, frontend/src/main.tsx, frontend/src/api.ts",
  commands_run: "python -m compileall backend; npm run build; uvicorn backend.app.main:app --reload",
  decisions:
    "Use Cognee Platform when tenant env vars exist. Keep local JSON only for project metadata and timeline proof.",
  blockers: "Need a stronger demo path, Codex session memory, and visible lifecycle proof for judges.",
  next_tasks:
    "Add Run Demo, remember coding-session summaries, show memory timeline, and ask morning brief recall questions.",
};

const lifecycleSteps = [
  { name: "remember()", detail: "notes, URLs, files, sessions" },
  { name: "recall()", detail: "morning brief and next actions" },
  { name: "improve()", detail: "graph enrichment after work" },
  { name: "forget()", detail: "project memory pruning" },
];

const judgePrompts = [
  "What was I working on yesterday?",
  "What files matter for the next coding session?",
  "What should I fix next?",
];

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [events, setEvents] = useState<MemoryEvent[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [newName, setNewName] = useState("Hackathon Memory Agent");
  const [newDescription, setNewDescription] = useState("A persistent project brain powered by Cognee.");
  const [title, setTitle] = useState("Last night's context");
  const [content, setContent] = useState(demoMemory);
  const [url, setUrl] = useState("");
  const [session, setSession] = useState<SessionMemory>(demoSession);
  const [query, setQuery] = useState(judgePrompts[0]);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [busy, setBusy] = useState(false);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedId),
    [projects, selectedId],
  );

  const recentSources = useMemo(() => {
    const sources = events
      .filter((event) => event.lifecycle === "remember()")
      .map((event) => event.source)
      .slice(0, 4);
    return sources.length ? `Related remembered sources: ${Array.from(new Set(sources)).join(", ")}` : undefined;
  }, [events]);

  const rememberedSourceCount = useMemo(
    () => events.filter((event) => event.lifecycle === "remember()").length,
    [events],
  );

  const lastLifecycle = events[0]?.lifecycle ?? "waiting";
  const selectedDataset = selectedId ? `project-${selectedId}` : "No dataset selected";

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
    getProjects()
      .then((items) => {
        setProjects(items);
        setSelectedId(items[0]?.id ?? "");
      })
      .catch((error) => push("system", "system", "Backend not ready", error.message));
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setEvents([]);
      return;
    }
    loadEvents(selectedId);
  }, [selectedId]);

  function push(kind: FeedItem["kind"], source: string, titleText: string, body: string, related?: string) {
    setFeed((items) => [{ kind, source, title: titleText, body, related }, ...items].slice(0, 16));
  }

  async function loadEvents(projectId: string) {
    const items = await getProjectEvents(projectId);
    setEvents(items);
  }

  async function refreshEvents(projectId = selectedId) {
    if (projectId) {
      await loadEvents(projectId);
    }
  }

  async function withBusy(action: () => Promise<void>) {
    setBusy(true);
    try {
      await action();
    } catch (error) {
      push("system", "system", "Request failed", error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  function requireProject() {
    if (!selectedId) {
      throw new Error("Create or select a project first.");
    }
    return selectedId;
  }

  async function ask(projectId: string, question: string) {
    const result = await recall(projectId, question);
    push("answer", "recall()", question, result.answer, recentSources);
    await refreshEvents(projectId);
  }

  function handleCreateProject(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const project = await createProject(newName, newDescription);
      setProjects((items) => [project, ...items]);
      setSelectedId(project.id);
      push("system", "project", "Project created", `${project.name} is ready for Cognee memory.`);
      await refreshEvents(project.id);
    });
  }

  function handleRememberText(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const projectId = requireProject();
      await rememberText(projectId, title, content);
      push("memory", "note", "Remembered note", content);
      await refreshEvents(projectId);
    });
  }

  function handleRememberSession(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const projectId = requireProject();
      await rememberSession(projectId, session);
      push("memory", "session", "Remembered Codex session", session.summary);
      await refreshEvents(projectId);
    });
  }

  function handleRememberUrl(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const projectId = requireProject();
      await rememberUrl(projectId, url);
      push("memory", "url", "Remembered URL", url);
      setUrl("");
      await refreshEvents(projectId);
    });
  }

  function handleFileChange(file: File | null) {
    if (!file) return;
    withBusy(async () => {
      const projectId = requireProject();
      await rememberFile(projectId, file);
      push("memory", "file", "Remembered file", file.name);
      await refreshEvents(projectId);
    });
  }

  function handleRecall(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      await ask(requireProject(), query);
    });
  }

  function handleMorningBrief() {
    const morningPrompt =
      "Give me a concise morning context brief with yesterday's decisions, blockers, files that matter, and next actions.";
    setQuery(morningPrompt);
    withBusy(async () => {
      await ask(requireProject(), morningPrompt);
    });
  }

  function handleImprove() {
    withBusy(async () => {
      const projectId = requireProject();
      await improve(projectId);
      push("system", "improve()", "Memory improved", "Cognee enriched this project memory graph.");
      await refreshEvents(projectId);
    });
  }

  function handleForget() {
    withBusy(async () => {
      const projectId = requireProject();
      await forget(projectId);
      push("system", "forget()", "Dataset forgotten", "The selected project's Cognee dataset was pruned.");
      await refreshEvents(projectId);
    });
  }

  function handleRunDemo() {
    withBusy(async () => {
      let projectId = selectedId;
      if (!projectId) {
        const project = await createProject("Where's My Context Demo", "Judge-ready coding-agent memory demo.");
        setProjects((items) => [project, ...items]);
        setSelectedId(project.id);
        projectId = project.id;
      }

      await rememberSession(projectId, demoSession);
      push("memory", "session", "Demo session remembered", demoSession.summary);

      await rememberText(projectId, "Demo project context", demoMemory);
      push("memory", "note", "Demo context remembered", demoMemory);

      await improve(projectId);
      push("system", "improve()", "Memory graph improved", "Cognee enriched the demo project memory.");

      for (const prompt of judgePrompts) {
        setQuery(prompt);
        await ask(projectId, prompt);
      }
      await refreshEvents(projectId);
    });
  }

  function updateSession(key: keyof SessionMemory, value: string) {
    setSession((current) => ({ ...current, [key]: value }));
  }

  return (
    <main className="shell">
      <section className="workspace">
        <aside className="sidebar">
          <div className="brand">
            <Brain size={28} />
            <div>
              <h1>Where's My Context?</h1>
              <p>Persistent Cognee memory for agents that should not wake up cold.</p>
            </div>
          </div>

          <button className="demo-button" disabled={busy} onClick={handleRunDemo} type="button">
            <Play size={18} />
            Run Demo
          </button>

          <section className="panel lifecycle">
            <h2>Cognee Lifecycle</h2>
            {lifecycleSteps.map((step) => (
              <div className="lifecycle-step" key={step.name}>
                <span>{step.name}</span>
                <p>{step.detail}</p>
              </div>
            ))}
          </section>

          <section className="panel proof-panel">
            <div className="panel-heading">
              <ShieldCheck size={20} />
              <h2>Memory Proof</h2>
            </div>
            <div className="proof-grid">
              <span>Provider</span>
              <strong>{health?.memory_mode === "cloud" ? "Cognee Cloud" : "Local Cognee SDK"}</strong>
              <span>Dataset</span>
              <strong>{selectedDataset}</strong>
              <span>Remembered</span>
              <strong>{rememberedSourceCount} sources</strong>
              <span>Last call</span>
              <strong>{lastLifecycle}</strong>
            </div>
          </section>

          <form className="panel" onSubmit={handleCreateProject}>
            <h2>Project Brain</h2>
            <label>
              Name
              <input value={newName} onChange={(event) => setNewName(event.target.value)} />
            </label>
            <label>
              Description
              <textarea value={newDescription} onChange={(event) => setNewDescription(event.target.value)} />
            </label>
            <button disabled={busy} type="submit">
              <Sparkles size={18} />
              Create
            </button>
          </form>

          <section className="panel">
            <h2>Memory Spaces</h2>
            <div className="project-list">
              {projects.map((project) => (
                <button
                  className={project.id === selectedId ? "project active" : "project"}
                  key={project.id}
                  onClick={() => setSelectedId(project.id)}
                  type="button"
                >
                  <strong>{project.name}</strong>
                  <span>{project.description || project.id}</span>
                </button>
              ))}
              {projects.length === 0 ? <p className="muted">No project yet.</p> : null}
            </div>
          </section>
        </aside>

        <section className="main-grid">
          <div className="topbar">
            <div>
              <span className="eyebrow">Selected Memory</span>
              <h2>{selectedProject?.name ?? "Create a project to begin"}</h2>
            </div>
            <div className="actions">
              <button disabled={busy || !selectedId} onClick={handleImprove} type="button">
                <RefreshCcw size={18} />
                Improve
              </button>
              <button className="danger" disabled={busy || !selectedId} onClick={handleForget} type="button">
                <Trash2 size={18} />
                Forget
              </button>
            </div>
          </div>

          <section className="focus-grid">
            <form className="panel session-panel" onSubmit={handleRememberSession}>
              <div className="panel-heading">
                <Code2 size={20} />
                <h2>Codex Session Memory</h2>
              </div>
              <label>
                Session summary
                <textarea value={session.summary} onChange={(event) => updateSession("summary", event.target.value)} />
              </label>
              <div className="two-col">
                <label>
                  Files changed
                  <textarea
                    value={session.files_changed}
                    onChange={(event) => updateSession("files_changed", event.target.value)}
                  />
                </label>
                <label>
                  Commands run
                  <textarea
                    value={session.commands_run}
                    onChange={(event) => updateSession("commands_run", event.target.value)}
                  />
                </label>
              </div>
              <div className="two-col">
                <label>
                  Decisions
                  <textarea value={session.decisions} onChange={(event) => updateSession("decisions", event.target.value)} />
                </label>
                <label>
                  Blockers
                  <textarea value={session.blockers} onChange={(event) => updateSession("blockers", event.target.value)} />
                </label>
              </div>
              <label>
                Next tasks
                <textarea value={session.next_tasks} onChange={(event) => updateSession("next_tasks", event.target.value)} />
              </label>
              <button disabled={busy || !selectedId} type="submit">
                <ShieldCheck size={18} />
                Remember Session
              </button>
            </form>

            <section className="panel timeline-panel">
              <div className="panel-heading">
                <Clock3 size={20} />
                <h2>Memory Timeline</h2>
              </div>
              <div className="timeline">
                {events.slice(0, 12).map((event) => (
                  <article className="timeline-item" key={event.id}>
                    <div>
                      <span className="badge">{event.lifecycle}</span>
                      <span className="source">{event.source}</span>
                    </div>
                    <strong>{event.title}</strong>
                    <p>{event.detail}</p>
                  </article>
                ))}
                {events.length === 0 ? <p className="muted">Lifecycle events will appear here.</p> : null}
              </div>
            </section>
          </section>

          <section className="memory-grid">
            <form className="panel tall" onSubmit={handleRememberText}>
              <h2>Remember Note</h2>
              <label>
                Title
                <input value={title} onChange={(event) => setTitle(event.target.value)} />
              </label>
              <label className="grow">
                Text, notes, decisions, logs
                <textarea value={content} onChange={(event) => setContent(event.target.value)} />
              </label>
              <button disabled={busy || !selectedId} type="submit">
                <Brain size={18} />
                Store Memory
              </button>
            </form>

            <div className="stack">
              <form className="panel" onSubmit={handleRememberUrl}>
                <h2>Ingest URL</h2>
                <label>
                  URL
                  <input placeholder="https://..." value={url} onChange={(event) => setUrl(event.target.value)} />
                </label>
                <button disabled={busy || !selectedId || !url} type="submit">
                  <Link size={18} />
                  Remember URL
                </button>
              </form>

              <section className="panel">
                <h2>Upload File</h2>
                <label className="file-drop">
                  <FileUp size={22} />
                  <span>PDFs, docs, notes, logs</span>
                  <input onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)} type="file" />
                </label>
              </section>
            </div>
          </section>

          <section className="recall-row">
            <form className="panel recall" onSubmit={handleRecall}>
              <h2>Recall</h2>
              <div className="prompt-row">
                {judgePrompts.map((prompt) => (
                  <button className="secondary" key={prompt} onClick={() => setQuery(prompt)} type="button">
                    <ListChecks size={16} />
                    {prompt}
                  </button>
                ))}
              </div>
              <div className="query-row">
                <input value={query} onChange={(event) => setQuery(event.target.value)} />
                <button disabled={busy || !selectedId} type="submit">
                  <Search size={18} />
                  Ask
                </button>
              </div>
              <button className="secondary" disabled={busy || !selectedId} onClick={handleMorningBrief} type="button">
                <Lightbulb size={18} />
                Morning Brief
              </button>
            </form>
          </section>

          <section className="feed">
            {feed.map((item, index) => (
              <article className={`feed-item ${item.kind}`} key={`${item.title}-${index}`}>
                <div className="feed-icon">
                  {item.kind === "answer" ? <MessageSquareText size={18} /> : <Brain size={18} />}
                </div>
                <div>
                  <div className="feed-meta">
                    <span className="source">{item.source}</span>
                    {item.related ? <span>{item.related}</span> : null}
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              </article>
            ))}
            {feed.length === 0 ? (
              <article className="empty-state">
                <Brain size={28} />
                <p>Run the demo, ask what happened yesterday, then watch Cognee recall the session context.</p>
              </article>
            ) : null}
          </section>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
