"use client";

import { useState } from "react";
import { SampleDataBanner } from "@/components/SampleDataBanner";
import { StatusBadge } from "@/components/FitBadge";
import { MOCK_CONTACTS, MOCK_OUTREACH } from "@/lib/mockData";
import { OutreachMessage } from "@/lib/types";

export default function ContactsPage() {
  const [outreach, setOutreach] = useState<OutreachMessage[]>(MOCK_OUTREACH);

  function markSent(id: string) {
    setOutreach((prev) => prev.map((o) => (o.id === id ? { ...o, status: "sent" } : o)));
  }
  function markSkipped(id: string) {
    setOutreach((prev) => prev.map((o) => (o.id === id ? { ...o, status: "skipped" } : o)));
  }

  return (
    <main className="max-w-4xl mx-auto px-6 py-10 flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold">Contacts & Outreach</h1>
        <p className="text-sm text-neutral-500 mt-1">
          People found per application via safe sources (careers pages, GitHub, public
          directories) — never LinkedIn scraping. Drafts only; sending on LinkedIn stays a
          manual, human action.
        </p>
      </div>

      <SampleDataBanner agent="Connection Finder + Outreach Writer" />

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Draft outreach</h2>
        {outreach.map((o) => (
          <div key={o.id} className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium">{o.contactName}</span>
                <span className="text-neutral-500"> · {o.company} · </span>
                <span className="text-xs uppercase tracking-wide text-neutral-400">{o.variant.replace("_", " ")}</span>
              </div>
              <StatusBadge status={o.status} />
            </div>
            <p className="text-sm rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3 text-neutral-700 dark:text-neutral-300">
              {o.draft}
            </p>
            {o.status === "draft" && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => markSent(o.id)}
                  className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-1.5"
                >
                  Copy & mark sent
                </button>
                <button
                  onClick={() => markSkipped(o.id)}
                  className="rounded-lg border border-neutral-300 dark:border-neutral-700 text-sm font-medium px-4 py-1.5 hover:bg-neutral-50 dark:hover:bg-neutral-900"
                >
                  Skip
                </button>
              </div>
            )}
          </div>
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">People found</h2>
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 divide-y divide-neutral-200 dark:divide-neutral-800">
          {MOCK_CONTACTS.map((c) => (
            <div key={c.id} className="flex items-center justify-between px-4 py-3 text-sm">
              <div>
                <span className="font-medium">{c.name}</span>
                <span className="text-neutral-500"> · {c.company} · </span>
                <span className="capitalize text-neutral-500">{c.role.replace("_", " ")}</span>
              </div>
              <a href={c.profileUrl} target="_blank" rel="noreferrer" className="text-indigo-600 hover:text-indigo-800">
                Profile ↗
              </a>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
