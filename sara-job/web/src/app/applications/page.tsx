"use client";

import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/FitBadge";
import { api, API_URL } from "@/lib/api";
import { Application } from "@/lib/types";

const PENDING_CONFIRM_STATUSES = ["ready_for_human_submit", "needs_human_input"];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listApplications()
      .then(setApplications)
      .catch(() => setError("Couldn't reach the backend — is the FastAPI server running?"));
  }, []);

  const [opening, setOpening] = useState<Record<string, boolean>>({});

  async function confirm(id: string, submitted: boolean) {
    let status: string;
    let submittedAt: string | null;
    if (submitted) {
      const updated = await api.confirmApplicationSubmitted(id);
      status = updated.status;
      submittedAt = updated.submittedAt;
    } else {
      const updated = await api.markApplicationNotSubmitted(id);
      status = updated.status;
      submittedAt = null;
    }
    setApplications((prev) => prev?.map((a) => (a.id === id ? { ...a, status, submittedAt } : a)) ?? prev);
  }

  async function open(id: string) {
    setOpening((prev) => ({ ...prev, [id]: true }));
    try {
      await api.openApplication(id);
    } finally {
      setTimeout(() => setOpening((prev) => ({ ...prev, [id]: false })), 5000);
    }
  }

  return (
    <main className="max-w-4xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Applications</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Every submission Sara has made, with proof and status. Sara pre-fills each application
          in the background; click <strong>Open</strong> next to a role to pop it up already
          filled in — you just review and click Submit (Ashby rejects automated submit clicks as
          spam, so that click has to be real). Confirm below once you have.
        </p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {!error && !applications && <p className="text-sm text-neutral-500">Loading…</p>}

      {applications && applications.length === 0 && (
        <p className="text-sm text-neutral-500">No applications yet — approve a job and run the Applier.</p>
      )}

      {applications && applications.length > 0 && (
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-neutral-200 dark:border-neutral-800 text-neutral-500">
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Resume</th>
                <th className="px-4 py-3 font-medium">Via</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Submitted</th>
                <th className="px-4 py-3 font-medium">Proof</th>
                <th className="px-4 py-3 font-medium">Confirm</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((a) => (
                <tr key={a.id} className="border-b border-neutral-100 dark:border-neutral-900 last:border-0">
                  <td className="px-4 py-3 font-medium capitalize">{a.company}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <a href={a.jobUrl} target="_blank" rel="noreferrer" className="hover:text-indigo-600">
                        {a.title}
                      </a>
                      {PENDING_CONFIRM_STATUSES.includes(a.status) && (
                        <button
                          onClick={() => open(a.id)}
                          disabled={opening[a.id]}
                          className="shrink-0 rounded-md border border-indigo-300 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 text-xs font-medium px-2 py-0.5 hover:bg-indigo-50 dark:hover:bg-indigo-950 disabled:opacity-50"
                        >
                          {opening[a.id] ? "Opening…" : "Open"}
                        </button>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-neutral-500">{a.resumeVariant || "—"}</td>
                  <td className="px-4 py-3 text-neutral-500 capitalize">{a.submittedVia || "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-4 py-3 text-neutral-500">
                    {a.submittedAt ? new Date(a.submittedAt).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-neutral-500">
                    {a.proofScreenshotUrl ? (
                      <a
                        href={`${API_URL}${a.proofScreenshotUrl}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-600 hover:text-indigo-800"
                      >
                        View
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {PENDING_CONFIRM_STATUSES.includes(a.status) ? (
                      <div className="flex items-center gap-2 whitespace-nowrap">
                        <button
                          onClick={() => confirm(a.id, true)}
                          className="rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-2.5 py-1"
                        >
                          Submitted
                        </button>
                        <button
                          onClick={() => confirm(a.id, false)}
                          className="rounded-md border border-neutral-300 dark:border-neutral-700 text-xs font-medium px-2.5 py-1 hover:bg-neutral-50 dark:hover:bg-neutral-900"
                        >
                          Not yet
                        </button>
                      </div>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
