// Client for the real FastAPI backend (jarvis/api/main.py). Per the locked
// doc: "Frontend never touches agents or the DB directly — everything goes
// through the FastAPI REST layer."

import { Application, Job } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => apiFetch<{ status: string }>("/api/health"),
  listJobs: (status?: string) =>
    apiFetch<Job[]>(`/api/jobs${status ? `?status=${status}` : ""}`),
  approveJob: (id: string) => apiFetch<Job>(`/api/jobs/${id}/approve`, { method: "POST" }),
  skipJob: (id: string) => apiFetch<Job>(`/api/jobs/${id}/skip`, { method: "POST" }),
  listApplications: () => apiFetch<Application[]>("/api/applications"),
  confirmApplicationSubmitted: (id: string) =>
    apiFetch<{ id: string; status: string; submittedAt: string }>(`/api/applications/${id}/confirm-submitted`, { method: "POST" }),
  markApplicationNotSubmitted: (id: string) =>
    apiFetch<{ id: string; status: string }>(`/api/applications/${id}/mark-not-submitted`, { method: "POST" }),
  openApplication: (id: string) =>
    apiFetch<{ id: string; status: string }>(`/api/applications/${id}/open`, { method: "POST" }),
};
