"use client";

import { useState } from "react";
import { SampleDataBanner } from "@/components/SampleDataBanner";
import { MOCK_AUDIT_LOG } from "@/lib/mockData";

const CAPS = [
  { label: "Applications per site per day", value: 15 },
  { label: "Outreach messages per day", value: 20 },
  { label: "LinkedIn actions per day", value: 0, note: "always 0 — drafts only, never automated" },
];

export default function AuditPage() {
  const [killed, setKilled] = useState(false);

  return (
    <main className="max-w-3xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Audit & Guardrails</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Every action and strategy version is logged. Rate/volume caps are fixed, not
          learnable — they protect your accounts regardless of what the strategy profile thinks
          is a good idea.
        </p>
      </div>

      <SampleDataBanner agent="Guardrails layer" />

      <div className={`rounded-xl border p-5 flex items-center justify-between ${killed ? "border-red-300 dark:border-red-900 bg-red-50 dark:bg-red-950/30" : "border-neutral-200 dark:border-neutral-800"}`}>
        <div>
          <h2 className="font-semibold">{killed ? "Sara is paused" : "Sara is active"}</h2>
          <p className="text-sm text-neutral-500 mt-0.5">
            {killed
              ? "All agents are halted — no scraping, scoring, applying, or messaging until resumed."
              : "One switch halts everything: scraping, applying, messaging."}
          </p>
        </div>
        <button
          onClick={() => setKilled((k) => !k)}
          className={`rounded-lg text-sm font-semibold px-4 py-2 ${
            killed
              ? "bg-emerald-600 hover:bg-emerald-700 text-white"
              : "bg-red-600 hover:bg-red-700 text-white"
          }`}
        >
          {killed ? "Resume Sara" : "Kill switch"}
        </button>
      </div>

      <section className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5">
        <h2 className="font-semibold mb-3">Fixed rate/volume caps</h2>
        <div className="flex flex-col gap-2 text-sm">
          {CAPS.map((c) => (
            <div key={c.label} className="flex items-center justify-between">
              <span className="text-neutral-600 dark:text-neutral-400">
                {c.label}{c.note && <span className="text-xs text-neutral-400"> — {c.note}</span>}
              </span>
              <span className="font-medium">{c.value}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-semibold">Action log</h2>
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 divide-y divide-neutral-200 dark:divide-neutral-800">
          {MOCK_AUDIT_LOG.map((l) => (
            <div key={l.id} className="px-4 py-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{l.actor}</span>
                <span className="text-xs text-neutral-500">{new Date(l.createdAt).toLocaleString()}</span>
              </div>
              <p className="text-neutral-600 dark:text-neutral-400 mt-0.5">{l.details}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
