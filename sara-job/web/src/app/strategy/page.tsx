"use client";

import { useState } from "react";
import { SampleDataBanner } from "@/components/SampleDataBanner";
import { StatusBadge } from "@/components/FitBadge";
import { MOCK_STRATEGY_VERSIONS } from "@/lib/mockData";
import { StrategyProfileVersion } from "@/lib/types";

const MIN_SAMPLE = 15;

export default function StrategyPage() {
  const [versions, setVersions] = useState<StrategyProfileVersion[]>(MOCK_STRATEGY_VERSIONS);

  function decide(version: number, status: StrategyProfileVersion["status"]) {
    setVersions((prev) => prev.map((v) => (v.version === version ? { ...v, status } : v)));
  }

  const sorted = [...versions].sort((a, b) => b.version - a.version);

  return (
    <main className="max-w-3xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Strategy Profile</h1>
        <p className="text-sm text-neutral-500 mt-1">
          A versioned playbook (resume weights, outreach tone, track priority, follow-up
          timing) that Reflection tunes nightly. Bounded action space only — it can never
          invent new actions or flip anything to auto-submit. You veto every change.
        </p>
      </div>

      <SampleDataBanner agent="Reflection + Strategy Profile" />

      <div className="rounded-lg bg-neutral-50 dark:bg-neutral-900 text-sm px-4 py-3 text-neutral-600 dark:text-neutral-400">
        Minimum sample size before a change is even proposed: ~{MIN_SAMPLE}-20 outcomes per bucket.
        Below that, Sara runs on defaults. ~15% of applications always stay exploration outside
        current beliefs, so the strategy never calcifies.
      </div>

      {sorted.map((v) => (
        <div key={v.version} className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-semibold">Version {v.version}</span>
              <StatusBadge status={v.status} />
            </div>
            <span className="text-xs text-neutral-500">{new Date(v.createdAt).toLocaleString()}</span>
          </div>
          <p className="text-sm text-neutral-700 dark:text-neutral-300">{v.summary}</p>
          <ul className="text-sm text-neutral-600 dark:text-neutral-400 list-disc pl-5 flex flex-col gap-1">
            {v.changes.map((c, i) => <li key={i}>{c}</li>)}
          </ul>
          <p className="text-xs text-neutral-500">
            Sample size: {v.sampleSize}{" "}
            {v.sampleSize < MIN_SAMPLE && v.status === "pending_review" && "— below minimum, held for review"}
          </p>
          {v.status === "pending_review" && (
            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={() => decide(v.version, "approved")}
                className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-1.5"
              >
                Approve
              </button>
              <button
                onClick={() => decide(v.version, "rejected")}
                className="rounded-lg border border-neutral-300 dark:border-neutral-700 text-sm font-medium px-4 py-1.5 hover:bg-neutral-50 dark:hover:bg-neutral-900"
              >
                Reject
              </button>
            </div>
          )}
          {v.status === "approved" && v.version !== 1 && (
            <button
              onClick={() => decide(v.version, "rolled_back")}
              className="self-start text-sm text-red-600 hover:text-red-800"
            >
              Roll back this version
            </button>
          )}
        </div>
      ))}
    </main>
  );
}
