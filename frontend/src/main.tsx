import { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Brain,
  FileUp,
  Lightbulb,
  Link,
  MessageSquareText,
  RefreshCcw,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  Project,
  createProject,
  forget,
  getProjects,
  improve,
  recall,
  rememberFile,
  rememberText,
  rememberUrl,
} from "./api";
import "./styles.css";

type FeedItem = {
  kind: "memory" | "answer" | "system";
  title: string;
  body: string;
};

const demoMemory = `Doug is the groom. The wedding is Sunday.
We chose FastAPI because Cognee is Python-native and lets us ship memory endpoints quickly.
Yesterday's blocker: file ingestion failed for large PDFs.
Next action: fix upload validation, then generate the morning context brief.`;

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [newName, setNewName] = useState("Hackathon Memory Agent");
  const [newDescription, setNewDescription] = useState("A persistent project brain powered by Cognee.");
  const [title, setTitle] = useState("Last night's context");
  const [content, setContent] = useState(demoMemory);
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("What should I work on today?");
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [busy, setBusy] = useState(false);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedId),
    [projects, selectedId],
  );

  useEffect(() => {
    getProjects()
      .then((items) => {
        setProjects(items);
        setSelectedId(items[0]?.id ?? "");
      })
      .catch((error) => push("system", "Backend not ready", error.message));
  }, []);

  function push(kind: FeedItem["kind"], titleText: string, body: string) {
    setFeed((items) => [{ kind, title: titleText, body }, ...items].slice(0, 12));
  }

  async function withBusy(action: () => Promise<void>) {
    setBusy(true);
    try {
      await action();
    } catch (error) {
      push("system", "Request failed", error instanceof Error ? error.message : String(error));
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

  function handleCreateProject(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const project = await createProject(newName, newDescription);
      setProjects((items) => [project, ...items]);
      setSelectedId(project.id);
      push("system", "Project created", `${project.name} is ready for memory.`);
    });
  }

  function handleRememberText(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const projectId = requireProject();
      await rememberText(projectId, title, content);
      push("memory", "Remembered note", content);
    });
  }

  function handleRememberUrl(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const projectId = requireProject();
      await rememberUrl(projectId, url);
      push("memory", "Remembered URL", url);
      setUrl("");
    });
  }

  function handleFileChange(file: File | null) {
    if (!file) return;
    withBusy(async () => {
      const projectId = requireProject();
      await rememberFile(projectId, file);
      push("memory", "Remembered file", file.name);
    });
  }

  function handleRecall(event: FormEvent) {
    event.preventDefault();
    withBusy(async () => {
      const projectId = requireProject();
      const result = await recall(projectId, query);
      push("answer", query, result.answer);
    });
  }

  function handleMorningBrief() {
    setQuery("Give me a concise morning context brief: yesterday's decisions, blockers, and next actions.");
  }

  function handleImprove() {
    withBusy(async () => {
      const projectId = requireProject();
      await improve(projectId);
      push("system", "Memory improved", "Cognee enriched this project memory graph.");
    });
  }

  function handleForget() {
    withBusy(async () => {
      const projectId = requireProject();
      await forget(projectId);
      push("system", "Dataset forgotten", "The selected project's Cognee dataset was pruned.");
    });
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

          <div className="panel">
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
          </div>
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

          <section className="memory-grid">
            <form className="panel tall" onSubmit={handleRememberText}>
              <h2>Remember</h2>
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

              <div className="panel">
                <h2>Upload File</h2>
                <label className="file-drop">
                  <FileUp size={22} />
                  <span>PDFs, docs, notes, logs</span>
                  <input onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)} type="file" />
                </label>
              </div>
            </div>
          </section>

          <section className="recall-row">
            <form className="panel recall" onSubmit={handleRecall}>
              <h2>Recall</h2>
              <div className="query-row">
                <input value={query} onChange={(event) => setQuery(event.target.value)} />
                <button disabled={busy || !selectedId} type="submit">
                  <Search size={18} />
                  Ask
                </button>
              </div>
              <button className="secondary" onClick={handleMorningBrief} type="button">
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
                  <h3>{item.title}</h3>
                  <p>{item.body}</p>
                </div>
              </article>
            ))}
            {feed.length === 0 ? (
              <article className="empty-state">
                <Brain size={28} />
                <p>Add demo memory, ask what happened yesterday, then improve or forget the dataset.</p>
              </article>
            ) : null}
          </section>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

