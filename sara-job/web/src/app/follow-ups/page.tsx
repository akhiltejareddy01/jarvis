"use client";

import { useState } from "react";
import { SampleDataBanner } from "@/components/SampleDataBanner";
import { StatusBadge } from "@/components/FitBadge";
import { gmailComposeUrl } from "@/lib/gmail";
import { MOCK_FOLLOWUPS } from "@/lib/mockData";
import { FollowUp } from "@/lib/types";

export default function FollowUpsPage() {
  const [items, setItems] = useState<FollowUp[]>(MOCK_FOLLOWUPS);

  function resolve(id: string, status: FollowUp["status"]) {
    setItems((prev) => prev.map((f) => (f.id === id ? { ...f, status } : f)));
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Follow-ups</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Auto-drafted nudges when an application gets 5-7 business days of silence.
        </p>
      </div>

      <SampleDataBanner agent="Follow-up autopilot" />

      {items.filter((f) => f.status === "pending").length === 0 && (
        <p className="text-sm text-neutral-500">No follow-ups due right now.</p>
      )}

      {items.map((f) => (
        <div key={f.id} className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium">{f.title}</span>
              <span className="text-neutral-500"> · {f.company}</span>
            </div>
            <StatusBadge status={f.status} />
          </div>
          <p className="text-xs text-neutral-500">Due {new Date(f.dueAt).toLocaleDateString()}</p>
          <p className="text-sm rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3 text-neutral-700 dark:text-neutral-300">
            {f.messageDraft}
          </p>
          {f.status === "pending" && (
            <div className="flex items-center gap-3">
              <a
                href={gmailComposeUrl({ to: f.recruiterEmail, subject: `Following up — ${f.title}`, body: f.messageDraft })}
                target="_blank"
                rel="noreferrer"
                onClick={() => resolve(f.id, "sent")}
                className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-1.5"
              >
                Open in Gmail →
              </a>
              <button
                onClick={() => resolve(f.id, "skipped")}
                className="rounded-lg border border-neutral-300 dark:border-neutral-700 text-sm font-medium px-4 py-1.5 hover:bg-neutral-50 dark:hover:bg-neutral-900"
              >
                Skip
              </button>
            </div>
          )}
        </div>
      ))}
    </main>
  );
}
