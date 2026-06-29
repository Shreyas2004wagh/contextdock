const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export type Project = {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
};

export type MemoryEvent = {
  id: string;
  project_id: string;
  lifecycle: string;
  source: string;
  title: string;
  detail: string;
  created_at: string;
};

export type SessionMemory = {
  summary: string;
  files_changed: string;
  commands_run: string;
  decisions: string;
  blockers: string;
  next_tasks: string;
};

export type Health = {
  status: string;
  memory_mode: "cloud" | "local";
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: options?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export function getHealth() {
  return request<Health>("/health");
}

export function getProjects() {
  return request<Project[]>("/projects");
}

export function createProject(name: string, description: string) {
  return request<Project>("/projects", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
}

export function getProjectEvents(projectId: string) {
  return request<MemoryEvent[]>(`/projects/${encodeURIComponent(projectId)}/events`);
}

export function rememberText(projectId: string, title: string, content: string) {
  return request<{ status: string }>("/memory/remember/text", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, title, content }),
  });
}

export function rememberUrl(projectId: string, url: string) {
  return request<{ status: string }>("/memory/remember/url", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, url }),
  });
}

export function rememberFile(projectId: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<{ status: string }>(`/memory/remember/file?project_id=${encodeURIComponent(projectId)}`, {
    method: "POST",
    body,
  });
}

export function rememberSession(projectId: string, session: SessionMemory) {
  return request<{ status: string }>("/memory/remember/session", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, ...session }),
  });
}

export function recall(projectId: string, query: string) {
  return request<{ answer: string }>("/memory/recall", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, query }),
  });
}

export function improve(projectId: string) {
  return request<{ status: string }>("/memory/improve", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}

export function forget(projectId: string) {
  return request<{ status: string }>("/memory/forget", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId }),
  });
}
