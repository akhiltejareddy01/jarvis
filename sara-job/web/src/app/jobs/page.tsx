"use client";

import { useEffect, useState } from "react";
import { FitBadge, StatusBadge } from "@/components/FitBadge";
import { api } from "@/lib/api";
import { Job } from "@/lib/types";

const FIT_ORDER = { strong: 0, medium: 1, weak: 2 } as const;

function JobCard({
  job,
  expanded,
  onToggleExpand,
  onDecide,
}: {
  job: Job;
  expanded: boolean;
  onToggleExpand: () => void;
  onDecide?: (action: "approve" | "skip") => void;
}) {
  return (
    <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold">{job.title}</h3>
            <FitBadge rating={job.fitRating} />
            {job.status !== "new" && <StatusBadge status={job.status} />}
          </div>
          <p className="text-sm text-neutral-500">
            {job.company} · {job.location || "location unknown"}{job.remote ? " · Remote" : ""} · {job.themeDay}
          </p>
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm font-medium text-neutral-400">
            {job.atsScore != null ? `ATS ${job.atsScore}%` : "Not tailored yet"}
          </div>
          {job.resumeUsed && <div className="text-xs text-neutral-500">{job.resumeUsed}</div>}
        </div>
      </div>

      <p className="text-sm text-neutral-700 dark:text-neutral-300">{job.fitReason ?? "Not scored yet."}</p>

      {job.coverLetterPreview && (
        <>
          <button
            onClick={onToggleExpand}
            className="self-start text-sm font-medium text-indigo-600 hover:text-indigo-800"
          >
            {expanded ? "Hide cover letter" : "Show cover letter"}
          </button>
          {expanded && (
            <p className="text-sm rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3 text-neutral-600 dark:text-neutral-400 whitespace-pre-wrap">
              {job.coverLetterPreview}
            </p>
          )}
        </>
      )}

      <div className="flex items-center gap-3 pt-1">
        {onDecide && (
          <>
            <button
              onClick={() => onDecide("approve")}
              className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-1.5"
            >
              Approve
            </button>
            <button
              onClick={() => onDecide("skip")}
              className="rounded-lg border border-neutral-300 dark:border-neutral-700 text-sm font-medium px-4 py-1.5 hover:bg-neutral-50 dark:hover:bg-neutral-900"
            >
              Skip
            </button>
          </>
        )}
        <a href={job.url} target="_blank" rel="noreferrer" className="text-sm text-neutral-500 hover:text-indigo-600 ml-auto">
          View posting ↗
        </a>
      </div>
    </div>
  );
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    api
      .listJobs()
      .then(setJobs)
      .catch(() => setError("Couldn't reach the backend — is `uvicorn jarvis.api.main:app` running on port 8000?"));
  }, []);

  async function decide(id: string, action: "approve" | "skip") {
    const updated = action === "approve" ? await api.approveJob(id) : await api.skipJob(id);
    setJobs((prev) => prev?.map((j) => (j.id === id ? { ...j, status: updated.status } : j)) ?? prev);
  }

  if (error) {
    return (
      <main className="max-w-4xl mx-auto px-6 py-10">
        <p className="text-sm text-red-600">{error}</p>
      </main>
    );
  }

  if (!jobs) {
    return (
      <main className="max-w-4xl mx-auto px-6 py-10">
        <p className="text-sm text-neutral-500">Loading jobs…</p>
      </main>
    );
  }

  const sorted = [...jobs].sort(
    (a, b) => (FIT_ORDER[a.fitRating ?? "weak"] ?? 3) - (FIT_ORDER[b.fitRating ?? "weak"] ?? 3)
  );
  const pending = sorted.filter((j) => j.status === "new");
  const approved = sorted.filter((j) => j.status === "approved");
  const skipped = sorted.filter((j) => j.status === "skipped");

  return (
    <main className="max-w-4xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Job Queue</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Ranked by fit. Approve to queue for application (semi-auto — you still confirm the
          actual submit), Skip to drop it. Live from Scout → JD Parser → Fit Scorer → Resume
          Selector → Cover Letter — the resume track, ATS score, and cover letter below are
          real, generated per job.
        </p>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-400">
          Needs your review ({pending.length})
        </h2>
        {pending.length === 0 && (
          <p className="text-sm text-neutral-500">Nothing pending — queue is clear.</p>
        )}
        {pending.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            expanded={expanded === job.id}
            onToggleExpand={() => setExpanded(expanded === job.id ? null : job.id)}
            onDecide={(action) => decide(job.id, action)}
          />
        ))}
      </section>

      {approved.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-400">
            Approved — ready to apply ({approved.length})
          </h2>
          {approved.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              expanded={expanded === job.id}
              onToggleExpand={() => setExpanded(expanded === job.id ? null : job.id)}
            />
          ))}
        </section>
      )}

      {skipped.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-400">
            Skipped ({skipped.length})
          </h2>
          <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 divide-y divide-neutral-200 dark:divide-neutral-800">
            {skipped.map((job) => (
              <div key={job.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{job.title}</span>
                  <span className="text-neutral-500">· {job.company}</span>
                </div>
                <div className="flex items-center gap-2">
                  <FitBadge rating={job.fitRating} />
                  <StatusBadge status={job.status} />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
