import { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Clock3,
  Code2,
  Copy,
  Database,
  FileUp,
  Github,
  GitBranch,
  Lightbulb,
  Link,
  ListChecks,
  MessageSquareText,
  Network,
  Play,
  RefreshCcw,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  API_BASE,
  AuthProviders,
  CurrentUser,
  Health,
  MemoryEvent,
  Project,
  SessionMemory,
  createProject,
  forget,
  getAuthProviders,
  getCurrentUser,
  getHealth,
  getProjectEvents,
  getProjects,
  improve,
  logout,
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

const demoMemory = `Release Atlas shipped a new pull request review flow yesterday.
The agent touched the FastAPI memory routes, the React command surface, and the Vercel deployment configuration.
The main decision was to keep Cognee Cloud as the persistent memory layer while local JSON stores only timeline metadata.
The active blocker is confirming the production OAuth callback configuration before rollout.
Next action: verify GitHub and Google sign-in, then ask Cognee for the release handoff brief.`;

const demoSession: SessionMemory = {
  summary:
    "Release Atlas is preparing an agent memory rollout that preserves product decisions, changed files, review status, and next actions across sessions.",
  files_changed: "backend/app/main.py, backend/app/auth.py, frontend/src/main.tsx, frontend/src/api.ts",
  commands_run: "python -m compileall backend; npm run build; curl /health; curl /auth/providers",
  decisions:
    "Use Cognee Cloud for persistent project memory. Keep user/session metadata separate from memory content.",
  blockers: "OAuth callback URLs need production verification before the agent memory workspace is shared.",
  next_tasks:
    "Sign in, create a memory space, run the live memory case, and review the Cognee handoff brief.",
};

const morningPrompt =
  "Give me a concise release handoff brief with decisions, blockers, files that matter, and next actions.";

const lifecycleSteps = [
  { name: "remember()", detail: "Store sessions, notes, files, and URLs." },
  { name: "recall()", detail: "Recover yesterday's project context." },
  { name: "improve()", detail: "Enrich the selected memory graph." },
  { name: "forget()", detail: "Prune a project dataset safely." },
];

const judgePrompts = [
  "What changed in the last agent session?",
  "Which files matter for the release handoff?",
  "What should the agent do next?",
];

const repositoryUrl = "https://github.com/Shreyas2004wagh/cogneeProject";

const caseStages = ["Trigger", "remember()", "improve()", "recall()", "Handoff Brief"];

const howItWorks = [
  {
    title: "Capture the work session",
    body: "Files, commands, decisions, blockers, notes, URLs, and uploads become structured memory inputs.",
  },
  {
    title: "Commit it to Cognee Cloud",
    body: "The backend writes each project source through Cognee remember() into a project-scoped dataset.",
  },
  {
    title: "Recover the next morning",
    body: "recall() turns the selected memory space into a useful brief for the agent's next action.",
  },
  {
    title: "Keep memory healthy",
    body: "improve() enriches the graph after a session, while forget() safely prunes an old memory space.",
  },
];

const architectureItems = [
  { icon: Code2, title: "React + Vite", body: "Product landing, live memory case, proof receipt, and builder controls." },
  { icon: Server, title: "FastAPI backend", body: "Project routes, Cognee lifecycle calls, uploads, and timeline metadata." },
  { icon: Database, title: "Cognee Cloud", body: "Persistent graph-vector memory scoped to each coding project." },
  { icon: GitBranch, title: "Vercel + Render", body: "Frontend on Vercel, backend on Render, local JSON only for event proof." },
];

function productText(value: string) {
  return [
    ["Run Demo", "Try Live Memory Case"],
    ["Run demo", "Try live memory case"],
    ["run demo", "try live memory case"],
    ["Where's My Context Demo", "Release Atlas"],
    ["judge-safe walkthrough", "memory workflow"],
    ["judges", "users"],
    ["judge", "user"],
    ["hackathon MVP", "agent memory workspace"],
    ["Hackathon", "Agent"],
    ["hackathon", "agent memory"],
    ["fix upload validation", "verify release handoff"],
    ["Fix upload validation", "Verify release handoff"],
  ].reduce((text, [from, to]) => text.split(from).join(to), value);
}

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [events, setEvents] = useState<MemoryEvent[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [authProviders, setAuthProviders] = useState<AuthProviders | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [newName, setNewName] = useState("Release Atlas");
  const [newDescription, setNewDescription] = useState("A persistent agent memory space powered by Cognee.");
  const [title, setTitle] = useState("Release handoff context");
  const [content, setContent] = useState(demoMemory);
  const [url, setUrl] = useState("");
  const [session, setSession] = useState<SessionMemory>(demoSession);
  const [query, setQuery] = useState(judgePrompts[0]);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [demoStage, setDemoStage] = useState("Workspace ready. Start a live memory case when you want context back.");
  const [morningBriefAnswer, setMorningBriefAnswer] = useState("");

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedId),
    [projects, selectedId],
  );

  const rememberedSourceCount = useMemo(
    () => events.filter((event) => event.lifecycle === "remember()").length,
    [events],
  );

  const sourceSummary = useMemo(() => {
    const counts = events
      .filter((event) => event.lifecycle === "remember()")
      .reduce<Record<string, number>>((summary, event) => {
        summary[event.source] = (summary[event.source] ?? 0) + 1;
        return summary;
      }, {});
    return Object.entries(counts);
  }, [events]);

  const lifecycleCounts = useMemo(() => {
    return events.reduce<Record<string, number>>((summary, event) => {
      summary[event.lifecycle] = (summary[event.lifecycle] ?? 0) + 1;
      return summary;
    }, {});
  }, [events]);

  const memoryGraphNodes = useMemo(() => {
    const remembered = sourceSummary.map(([source, count]) => ({
      label: source,
      meta: `${count} source${count === 1 ? "" : "s"}`,
      type: "source",
    }));
    const lifecycle = lifecycleSteps
      .map((step) => ({
        label: step.name,
        meta: `${lifecycleCounts[step.name] ?? 0} calls`,
        type: "lifecycle",
      }))
      .filter((node) => node.meta !== "0 calls");
    return [...remembered, ...lifecycle].slice(0, 8);
  }, [lifecycleCounts, sourceSummary]);

  const timelineEvents = useMemo(() => {
    const requiredLifecycle = ["recall()", "improve()", "remember()"];
    const selected = [...events.slice(0, 5)];
    for (const lifecycle of requiredLifecycle) {
      const hasLifecycle = selected.some((event) => event.lifecycle === lifecycle);
      const event = events.find((item) => item.lifecycle === lifecycle);
      if (!hasLifecycle && event) {
        selected.push(event);
      }
    }
    return Array.from(new Map(selected.map((event) => [event.id, event])).values()).slice(0, 8);
  }, [events]);

  const lastLifecycle = events[0]?.lifecycle ?? "waiting";
  const selectedDataset = selectedId ? `project-${selectedId}` : "No dataset selected";
  const latestAnswer = feed.find((item) => item.kind === "answer");
  const latestRecall = events.find((event) => event.lifecycle === "recall()");
  const providerLabel = health?.memory_mode === "cloud" ? "Cognee Cloud" : "Local Cognee SDK";
  const cloudModeLabel = health?.memory_mode === "cloud" ? "Cognee Cloud online" : "Local memory mode";
  const proofSourceLabels = sourceSummary.length
    ? sourceSummary.map(([source, count]) => `${source} ${count}`).join(", ")
    : "no sources yet";
  const visibleBrief =
    productText(
      morningBriefAnswer ||
        latestAnswer?.body ||
        "Start the live memory case to let Cognee reconstruct the latest decisions, blockers, files, and next action.",
    );
  const proofSummary = [
    "Where's My Context? memory receipt",
    `Provider: ${providerLabel}`,
    `Dataset: ${selectedDataset}`,
    `Remembered sources: ${rememberedSourceCount}`,
    `Lifecycle counts: remember() ${lifecycleCounts["remember()"] ?? 0}, improve() ${
      lifecycleCounts["improve()"] ?? 0
    }, recall() ${lifecycleCounts["recall()"] ?? 0}, forget() ${lifecycleCounts["forget()"] ?? 0}`,
    `Source labels: ${proofSourceLabels}`,
    `Latest recall question: ${productText(latestRecall?.title ?? latestAnswer?.title ?? "No recall yet")}`,
    `Morning brief excerpt: ${visibleBrief.slice(0, 360)}`,
  ].join("\n");
  const isSignedIn = Boolean(currentUser);

  useEffect(() => {
    getAuthProviders()
      .then(setAuthProviders)
      .catch(() => setAuthProviders(null));
    getCurrentUser()
      .then((result) => setCurrentUser(result.user))
      .catch(() => setCurrentUser(null));
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
    getProjects()
      .then((items) => {
        setProjects(items);
        const newestProject = [...items].sort((left, right) =>
          right.updated_at.localeCompare(left.updated_at),
        )[0];
        setSelectedId(newestProject?.id ?? "");
      })
      .catch((error) => push("system", "system", "Backend not ready", error.message));
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setEvents([]);
      setMorningBriefAnswer("");
      return;
    }
    loadEvents(selectedId, true);
  }, [selectedId]);

  function push(kind: FeedItem["kind"], source: string, titleText: string, body: string, related?: string) {
    setFeed((items) => [{ kind, source, title: titleText, body, related }, ...items].slice(0, 16));
  }

  async function loadEvents(projectId: string, syncMorningBrief = false) {
    const items = await getProjectEvents(projectId);
    setEvents(items);
    if (syncMorningBrief) {
      const briefEvent = items.find(
        (event) => event.lifecycle === "recall()" && event.title === morningPrompt,
      );
      setMorningBriefAnswer(briefEvent?.detail ?? "");
    }
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
      setDemoStage("Something needs attention before the memory workflow can continue.");
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

  function relatedSources() {
    const sources = events
      .filter((event) => event.lifecycle === "remember()")
      .map((event) => event.source)
      .slice(0, 4);
    return sources.length ? `Sources: ${Array.from(new Set(sources)).join(", ")}` : undefined;
  }

  async function ask(projectId: string, question: string, pinMorningBrief = false) {
    const result = await recall(projectId, question);
    push("answer", "recall()", question, result.answer, relatedSources());
    if (pinMorningBrief) {
      setMorningBriefAnswer(result.answer);
    }
    await refreshEvents(projectId);
  }

  async function createFreshDemoProject() {
    const project = await createProject("Release Atlas", "A live coding-agent memory space powered by Cognee.");
    setProjects((items) => [project, ...items]);
    setSelectedId(project.id);
    setMorningBriefAnswer("");
    setDemoStage("New memory space created.");
    await refreshEvents(project.id);
    return project.id;
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
      setDemoStage("recall() is asking Cognee for project context.");
      await ask(requireProject(), query, query === morningPrompt);
      setDemoStage("recall() returned context from the selected project memory.");
    });
  }

  function handleMorningBrief() {
    setQuery(morningPrompt);
    withBusy(async () => {
      setDemoStage("recall() is building the morning brief.");
      await ask(requireProject(), morningPrompt, true);
      setDemoStage("Morning brief recovered from Cognee memory.");
    });
  }

  function handleImprove() {
    withBusy(async () => {
      const projectId = requireProject();
      setDemoStage("improve() is enriching the memory graph.");
      await improve(projectId);
      push("system", "improve()", "Memory improved", "Cognee enriched this project memory graph.");
      await refreshEvents(projectId);
      setDemoStage("improve() completed for the selected project.");
    });
  }

  function handleForget() {
    withBusy(async () => {
      const projectId = requireProject();
      setDemoStage("forget() is pruning the selected dataset.");
      await forget(projectId);
      push("system", "forget()", "Dataset forgotten", "The selected project's Cognee dataset was pruned.");
      setMorningBriefAnswer("");
      await refreshEvents(projectId);
      setDemoStage("forget() completed. The selected memory space was pruned.");
    });
  }

  function handleFreshDemoProject() {
    withBusy(async () => {
      await createFreshDemoProject();
    });
  }

  function handleRunDemo() {
    withBusy(async () => {
      let projectId = selectedId;
      if (!projectId) {
        projectId = await createFreshDemoProject();
      }

      setDemoStage("remember() is storing the Codex session.");
      await rememberSession(projectId, demoSession);
      push("memory", "session", "Agent session remembered", demoSession.summary);
      await refreshEvents(projectId);

      setDemoStage("remember() is storing the project note.");
      await rememberText(projectId, "Release handoff context", demoMemory);
      push("memory", "note", "Release context remembered", demoMemory);
      await refreshEvents(projectId);

      setDemoStage("improve() is enriching the graph.");
      await improve(projectId);
      push("system", "improve()", "Memory graph improved", "Cognee enriched this project memory.");
      await refreshEvents(projectId);

      for (const prompt of judgePrompts) {
        setQuery(prompt);
        setDemoStage(`recall() is answering: ${prompt}`);
        await ask(projectId, prompt);
      }

      setQuery(morningPrompt);
      setDemoStage("recall() is producing the final morning brief.");
      await ask(projectId, morningPrompt, true);
      await refreshEvents(projectId);
      setDemoStage("Live memory case complete. The agent has the release context back.");
    });
  }

  async function handleCopyProofSummary() {
    try {
      try {
        if (!navigator.clipboard?.writeText) {
          throw new Error("Clipboard API unavailable");
        }
        await navigator.clipboard?.writeText(proofSummary);
      } catch {
        const textarea = document.createElement("textarea");
        textarea.value = proofSummary;
        textarea.setAttribute("readonly", "true");
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      push("system", "system", "Memory receipt copied", proofSummary);
    } catch (error) {
      push("system", "system", "Copy failed", error instanceof Error ? error.message : String(error));
    }
  }

  function updateSession(key: keyof SessionMemory, value: string) {
    setSession((current) => ({ ...current, [key]: value }));
  }

  function loginUrl(provider: "github" | "google") {
    return `${API_BASE}${authProviders?.[provider]?.login_url ?? `/auth/${provider}/login`}`;
  }

  function handleLogout() {
    withBusy(async () => {
      await logout();
      setCurrentUser(null);
      setProjects(await getProjects());
      setDemoStage("Signed out. Guest memory spaces are still available.");
    });
  }

  return (
    <main className="shell">
      <nav className="top-nav" aria-label="Primary navigation">
        <a className="brand-mark" href="#home">
          <Brain size={18} />
          <span>Where's My Context?</span>
        </a>
        <div className="nav-links">
          <a href={isSignedIn ? "#live-case" : "#how-it-works"}>{isSignedIn ? "Live Case" : "How It Works"}</a>
          <a href={isSignedIn ? "#proof" : "#signin"}>{isSignedIn ? "Proof" : "Sign In"}</a>
          <a href="#architecture">Architecture</a>
        </div>
        <div className="nav-actions">
          {currentUser ? (
            <>
              <span className="profile-chip">
                {currentUser.avatar_url ? <img alt="" src={currentUser.avatar_url} /> : <Brain size={15} />}
                {currentUser.name}
              </span>
              <button className="nav-button secondary-link" disabled={busy} onClick={handleLogout} type="button">
                Sign out
              </button>
            </>
          ) : (
            <>
              <a
                aria-disabled={!authProviders?.github.available}
                className={authProviders?.github.available ? "nav-button secondary-link" : "nav-button disabled-link"}
                href={authProviders?.github.available ? loginUrl("github") : undefined}
              >
                <Github size={16} />
                Start with GitHub
              </a>
              <a
                aria-disabled={!authProviders?.google.available}
                className={authProviders?.google.available ? "nav-button secondary-link" : "nav-button disabled-link"}
                href={authProviders?.google.available ? loginUrl("google") : undefined}
              >
                <Sparkles size={16} />
                Continue with Google
              </a>
            </>
          )}
          <a className="nav-button primary-link" href={isSignedIn ? "#live-case" : "#signin"}>
            <Play size={16} />
            {isSignedIn ? "Try Live Memory Case" : "Open Workspace"}
          </a>
        </div>
      </nav>

      <section className="story-hero" id="home">
        <div className="hero-copy">
          <span className="eyebrow">Agent Memory OS / powered by Cognee Cloud</span>
          <h1>Your AI agent remembers every project.</h1>
          <p>
            Persist files, decisions, blockers, commands, and release context so every coding agent can recover the
            exact memory it needs before it touches your codebase.
          </p>
          <div className="hero-actions">
            {!currentUser ? (
              <>
                <a
                  aria-disabled={!authProviders?.github.available}
                  className={authProviders?.github.available ? "demo-button auth-cta" : "demo-button auth-cta disabled-link"}
                  href={authProviders?.github.available ? loginUrl("github") : undefined}
                >
                  <Github size={18} />
                  Start with GitHub
                </a>
                <a
                  aria-disabled={!authProviders?.google.available}
                  className={authProviders?.google.available ? "secondary auth-cta" : "secondary auth-cta disabled-link"}
                  href={authProviders?.google.available ? loginUrl("google") : undefined}
                >
                  <Sparkles size={18} />
                  Continue with Google
                </a>
              </>
            ) : null}
            {isSignedIn ? (
              <>
                <button className="demo-button" disabled={busy} onClick={handleRunDemo} type="button">
                  <Play size={18} />
                  {busy ? "Running memory case..." : "Try Live Memory Case"}
                </button>
                <button className="secondary" disabled={busy} onClick={handleFreshDemoProject} type="button">
                  <Sparkles size={18} />
                  New Memory Space
                </button>
                <button className="ghost-button" disabled={busy || !selectedId} onClick={handleMorningBrief} type="button">
                  <Lightbulb size={18} />
                  Handoff Brief
                </button>
              </>
            ) : (
              <a className="ghost-button auth-cta" href="#signin">
                <ArrowRight size={18} />
                See how it works
              </a>
            )}
          </div>
          {authProviders && (!authProviders.github.available || !authProviders.google.available) ? (
            <p className="oauth-note">Sign-in activates when workspace authentication is configured.</p>
          ) : null}
          <div className="status-strip" aria-label="Demo execution status">
            {isSignedIn ? (
              <>
                <span className={lastLifecycle === "waiting" ? "" : "active"}>{lastLifecycle}</span>
                <span>{cloudModeLabel}</span>
                <span>{rememberedSourceCount} remembered sources</span>
              </>
            ) : (
              <>
                <span>Private workspace</span>
                <span>{cloudModeLabel}</span>
                <span>GitHub and Google sign-in</span>
              </>
            )}
          </div>
        </div>

        <section className="case-card" aria-label="Live coding session case">
          <div className="case-topline">
            <span className="source">CASE ARC-142</span>
            <span>{isSignedIn ? "Release agent memory" : "Workspace preview"}</span>
          </div>
          <div className="case-title-row">
            <div>
              <h2>{isSignedIn ? "Agent handoff recovered" : "Sign in to unlock the workspace"}</h2>
              <p>
                {isSignedIn
                  ? productText(selectedProject?.name ?? "Create or select a memory space to begin.")
                  : "Create private memory spaces, run Cognee lifecycle calls, and recover project context from any session."}
              </p>
            </div>
            <CheckCircle2 size={28} />
          </div>
          <div className="stage-rail" aria-label="Cognee case stages">
            {caseStages.map((stage, index) => (
              <div className={index === 0 || lifecycleCounts[stage] || stage === "Handoff Brief" ? "stage active" : "stage"} key={stage}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{stage}</strong>
              </div>
            ))}
          </div>
          <div className="case-brief-grid">
            <article>
              <span>Decision</span>
              <p>{session.decisions}</p>
            </article>
            <article>
              <span>Files</span>
              <p>{session.files_changed}</p>
            </article>
            <article>
              <span>Blocker</span>
              <p>{session.blockers}</p>
            </article>
            <article>
              <span>Next action</span>
              <p>{session.next_tasks}</p>
            </article>
          </div>
          <div className="case-actions">
            <span>{isSignedIn ? "Suggested next actions" : "Workspace unlocks"}</span>
            <p>
              {isSignedIn
                ? "Verify OAuth callbacks, review changed files, and ask Cognee for the next release action."
                : "Project memories, handoff briefs, source labels, lifecycle proof, and builder controls."}
            </p>
          </div>
          <p className="demo-stage">
            {isSignedIn ? demoStage : "Sign in to open the real memory workspace."}
          </p>
        </section>
      </section>

      {isSignedIn ? (
        <>
      <section className="live-workspace" id="live-case">
        <section className="brief-panel">
          <div className="panel-heading">
            <MessageSquareText size={20} />
            <div>
              <span className="eyebrow">Handoff Brief artifact</span>
              <h2>Recovered context</h2>
            </div>
          </div>
          <div className="brief-answer">
            <span>{morningBriefAnswer ? "Cognee recall answer" : "Waiting for recall()"}</span>
            <p>{visibleBrief}</p>
          </div>
        </section>

        <section className="panel proof-panel" id="proof">
          <div className="panel-heading split">
            <div className="panel-heading">
              <ShieldCheck size={20} />
              <div>
                <span className="eyebrow">Cognee Cloud Receipt</span>
                <h2>Live memory proof</h2>
              </div>
            </div>
            <button className="icon-button" disabled={!selectedId} onClick={handleCopyProofSummary} title="Copy Memory Receipt" type="button">
              <Copy size={17} />
            </button>
          </div>
          <div className="receipt-grid">
            <article>
              <span>Provider</span>
              <strong>{providerLabel}</strong>
            </article>
            <article>
              <span>Dataset</span>
              <strong>{selectedDataset}</strong>
            </article>
            <article>
              <span>Sources</span>
              <strong>{rememberedSourceCount}</strong>
            </article>
            <article>
              <span>Latest call</span>
              <strong>{lastLifecycle}</strong>
            </article>
          </div>
          <div className="source-strip">
            {sourceSummary.length ? (
              sourceSummary.map(([source, count]) => (
                <span className="source" key={source}>
                  {source} {count}
                </span>
              ))
            ) : (
              <span className="source">no sources yet</span>
            )}
          </div>
          <div className="memory-map" aria-label="Memory graph preview">
            <div className="graph-core">
              <Brain size={20} />
              <strong>Cognee</strong>
              <span>{health?.memory_mode === "cloud" ? "Cloud graph" : "Local graph"}</span>
            </div>
            <div className="graph-nodes">
              {memoryGraphNodes.length ? (
                memoryGraphNodes.map((node) => (
                  <span className={`graph-node ${node.type}`} key={`${node.type}-${node.label}`}>
                    <strong>{node.label}</strong>
                    <small>{node.meta}</small>
                  </span>
                ))
              ) : (
                <span className="graph-node empty">
                  <strong>waiting</strong>
                  <small>run case to draw proof</small>
                </span>
              )}
            </div>
          </div>
        </section>
      </section>

      <section className="proof-row">
        <section className="panel lifecycle">
          <div className="panel-heading">
            <Network size={20} />
            <h2>Cognee Lifecycle</h2>
          </div>
          <div className="lifecycle-grid">
            {lifecycleSteps.map((step) => (
              <div className="lifecycle-step" key={step.name}>
                <span>{step.name}</span>
                <strong>{lifecycleCounts[step.name] ?? 0}</strong>
                <p>{step.detail}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="panel timeline-panel">
          <div className="panel-heading">
            <Clock3 size={20} />
            <h2>Action trail</h2>
          </div>
          <div className="timeline">
            {timelineEvents.map((event) => (
              <article className="timeline-item" key={event.id}>
                <div>
                  <span className="badge">{event.lifecycle}</span>
                  <span className="source">{event.source}</span>
                </div>
                <strong>{productText(event.title)}</strong>
                <p>{productText(event.detail)}</p>
              </article>
            ))}
            {events.length === 0 ? <p className="muted">Lifecycle events will appear here.</p> : null}
          </div>
        </section>
      </section>

      <section className="story-section">
        <div className="section-heading">
          <span className="eyebrow">How it works</span>
          <h2>From yesterday's context to today's next action.</h2>
        </div>
        <div className="story-grid four">
          {howItWorks.map((item, index) => (
            <article className="story-card" key={item.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="story-section evidence-section">
        <div className="section-heading">
          <span className="eyebrow">Every brief shows its work</span>
          <h2>Source labels make the memory path visible.</h2>
        </div>
        <div className="evidence-grid">
          {["session", "note", "file", "url", "query", "system"].map((source) => (
            <article className="evidence-card" key={source}>
              <span className="source">{source}</span>
              <p>{sourceSummary.find(([name]) => name === source)?.[1] ?? 0} remembered events</p>
            </article>
          ))}
        </div>
      </section>

      <section className="story-section architecture-section" id="architecture">
        <div className="section-heading">
          <span className="eyebrow">Architecture</span>
          <h2>One product surface, real Cognee lifecycle calls.</h2>
        </div>
        <div className="story-grid four">
          {architectureItems.map((item) => {
            const Icon = item.icon;
            return (
              <article className="story-card architecture-card" key={item.title}>
                <Icon size={22} />
                <h3>{productText(item.title)}</h3>
                <p>{productText(item.body)}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="recall-feed-grid">
        <form className="panel recall" onSubmit={handleRecall}>
          <div className="panel-heading">
            <Search size={20} />
            <div>
              <span className="eyebrow">Recall prompts</span>
              <h2>Ask the memory space</h2>
            </div>
          </div>
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
              <ArrowRight size={18} />
              Ask
            </button>
          </div>
        </form>

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
              <p>Run the live case, ask what happened yesterday, then watch Cognee recall the session context.</p>
            </article>
          ) : null}
        </section>
      </section>

      <section className="story-section builder-section">
        <div className="section-heading">
          <span className="eyebrow">Builder controls</span>
          <h2>Build your own memory space when the live case is done.</h2>
        </div>
      </section>

      <section className="builder-grid">
        <form className="panel session-panel" onSubmit={handleRememberSession}>
          <div className="panel-heading">
            <Code2 size={20} />
            <h2>Agent Session Memory</h2>
          </div>
          <label>
            Session summary
            <textarea value={session.summary} onChange={(event) => updateSession("summary", event.target.value)} />
          </label>
          <div className="two-col">
            <label>
              Files changed
              <textarea value={session.files_changed} onChange={(event) => updateSession("files_changed", event.target.value)} />
            </label>
            <label>
              Commands run
              <textarea value={session.commands_run} onChange={(event) => updateSession("commands_run", event.target.value)} />
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

        <section className="builder-stack">
          <form className="panel" onSubmit={handleRememberText}>
            <h2>Remember Note</h2>
            <label>
              Title
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
            <label>
              Text, notes, decisions, logs
              <textarea value={content} onChange={(event) => setContent(event.target.value)} />
            </label>
            <button disabled={busy || !selectedId} type="submit">
              <Brain size={18} />
              Store Memory
            </button>
          </form>

          <div className="asset-grid">
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

        <aside className="builder-stack">
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
            <h2>{currentUser ? "My Memory Spaces" : "Guest Memory Spaces"}</h2>
            <div className="project-list">
              {projects.map((project) => (
                <button
                  className={project.id === selectedId ? "project active" : "project"}
                  key={project.id}
                  onClick={() => setSelectedId(project.id)}
                  type="button"
                >
                  <strong>{project.name}</strong>
                  <span>{productText(project.description || project.id)}</span>
                </button>
              ))}
              {projects.length === 0 ? <p className="muted">No project yet.</p> : null}
            </div>
          </section>

          <section className="panel selected-card">
            <span className="eyebrow">Selected Memory</span>
            <h2>{productText(selectedProject?.name ?? "Create a project to begin")}</h2>
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
          </section>
        </aside>
      </section>
        </>
      ) : (
        <>
          <section className="story-section landing-split" id="signin">
            <div className="section-heading">
              <span className="eyebrow">Start private</span>
              <h2>Sign in first. Then open your memory workspace.</h2>
              <p>
                The live product is gated behind OAuth so every memory space can belong to a real user. Guest previews stay public;
                project memory, recall, improve, forget, and builder controls unlock after sign-in.
              </p>
            </div>
            <div className="signin-card">
              <a
                aria-disabled={!authProviders?.github.available}
                className={authProviders?.github.available ? "demo-button auth-cta" : "demo-button auth-cta disabled-link"}
                href={authProviders?.github.available ? loginUrl("github") : undefined}
              >
                <Github size={18} />
                Start with GitHub
              </a>
              <a
                aria-disabled={!authProviders?.google.available}
                className={authProviders?.google.available ? "secondary auth-cta" : "secondary auth-cta disabled-link"}
                href={authProviders?.google.available ? loginUrl("google") : undefined}
              >
                <Sparkles size={18} />
                Continue with Google
              </a>
              {authProviders && (!authProviders.github.available || !authProviders.google.available) ? (
                <p className="muted">OAuth provider credentials are not configured on this backend yet.</p>
              ) : null}
            </div>
          </section>

          <section className="story-section" id="how-it-works">
            <div className="section-heading">
              <span className="eyebrow">How it works</span>
              <h2>From project activity to agent-ready memory.</h2>
            </div>
            <div className="story-grid four">
              {howItWorks.map((item, index) => (
                <article className="story-card" key={item.title}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="story-section evidence-section">
            <div className="section-heading">
              <span className="eyebrow">What unlocks after sign-in</span>
              <h2>Actual memory operations, not a marketing mock.</h2>
            </div>
            <div className="evidence-grid">
              {["remember()", "recall()", "improve()", "forget()", "source labels", "private spaces"].map((source) => (
                <article className="evidence-card" key={source}>
                  <span className="source">{source}</span>
                  <p>Available inside the authenticated workspace.</p>
                </article>
              ))}
            </div>
          </section>

          <section className="story-section architecture-section" id="architecture">
            <div className="section-heading">
              <span className="eyebrow">Architecture</span>
              <h2>OAuth identity, FastAPI orchestration, Cognee Cloud memory.</h2>
            </div>
            <div className="story-grid four">
              {architectureItems.map((item) => {
                const Icon = item.icon;
                return (
                  <article className="story-card architecture-card" key={item.title}>
                    <Icon size={22} />
                    <h3>{productText(item.title)}</h3>
                    <p>{productText(item.body)}</p>
                  </article>
                );
              })}
            </div>
          </section>
        </>
      )}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
