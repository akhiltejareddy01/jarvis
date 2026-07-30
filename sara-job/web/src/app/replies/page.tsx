"use client";

import { useState } from "react";
import { SampleDataBanner } from "@/components/SampleDataBanner";
import { StatusBadge } from "@/components/FitBadge";
import { gmailComposeUrl } from "@/lib/gmail";
import { MOCK_REPLIES } from "@/lib/mockData";
import { EmailReply } from "@/lib/types";

const CLASSIFICATION_LABEL: Record<EmailReply["classification"], string> = {
  confirmation: "Application received",
  assessment_invite: "Assessment invite",
  interview_invite: "Interview invite",
  offer: "Offer",
  rejection: "Rejection",
  info_request: "Info request",
  other: "Other",
};

const NOT_DRAFTABLE: EmailReply["classification"][] = ["confirmation"];

export default function RepliesPage() {
  const [replies, setReplies] = useState<EmailReply[]>(MOCK_REPLIES);

  function resolve(id: string, status: EmailReply["status"]) {
    setReplies((prev) => prev.map((r) => (r.id === id ? { ...r, status } : r)));
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Email Replies</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Reuses your{" "}
          <a href="https://github.com/akhiltejareddy01/email-agent" target="_blank" rel="noreferrer" className="text-indigo-600 hover:text-indigo-800">
            email-agent
          </a>{" "}
          project: reads Gmail (read + compose scopes only), classifies replies, drafts a
          response into Gmail Drafts. It never sends — you always review and send from Gmail
          yourself. Application-confirmation receipts are just logged; assessment invites,
          interview invites, offers, and rejections all get a drafted reply ready to go.
        </p>
      </div>

      <SampleDataBanner agent="Email layer (email-agent integration)" />

      {replies.map((r) => {
        const draftable = !NOT_DRAFTABLE.includes(r.classification);
        return (
          <div key={r.id} className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium">{r.subject}</span>
                <span className="text-neutral-500"> · {r.company} · {r.from}</span>
              </div>
              <StatusBadge status={r.status} />
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="rounded-full bg-neutral-100 dark:bg-neutral-900 px-2.5 py-0.5 font-medium">
                {CLASSIFICATION_LABEL[r.classification]}
              </span>
              <span className="text-neutral-500">{new Date(r.receivedAt).toLocaleString()}</span>
            </div>

            {draftable ? (
              <p className="text-sm rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3 text-neutral-700 dark:text-neutral-300">
                {r.draftResponse}
              </p>
            ) : (
              <p className="text-sm text-neutral-500 italic">
                No reply needed — logged as confirmation that the application went through.
              </p>
            )}

            {draftable && r.status === "pending_review" && (
              <div className="flex items-center gap-3">
                <a
                  href={gmailComposeUrl({ to: r.from, subject: `Re: ${r.subject}`, body: r.draftResponse })}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => resolve(r.id, "approved")}
                  className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-1.5"
                >
                  Open in Gmail →
                </a>
                <button
                  onClick={() => resolve(r.id, "skipped")}
                  className="rounded-lg border border-neutral-300 dark:border-neutral-700 text-sm font-medium px-4 py-1.5 hover:bg-neutral-50 dark:hover:bg-neutral-900"
                >
                  Skip
                </button>
              </div>
            )}
          </div>
        );
      })}
    </main>
  );
}
