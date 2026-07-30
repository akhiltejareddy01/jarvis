// Sample data shaped exactly like the real tables will be, so every page here
// is a preview of the real thing, not a placeholder. Swap for FastAPI calls
// once the Scout/JD Parser/Fit Scorer/Applier agents exist (see repo README).

import {
  AuditLogEntry,
  Contact,
  DailyReport,
  EmailReply,
  FollowUp,
  OutreachMessage,
  StrategyProfileVersion,
} from "./types";

// MOCK_JOBS was removed 2026-07-27 — /jobs now reads real data via lib/api.ts
// (jarvis/api/main.py). MOCK_APPLICATIONS was removed the same day for the
// same reason — /applications now reads real data too. Everything below is
// still mock, pending its own agent.

export const MOCK_CONTACTS: Contact[] = [
  {
    id: "c1",
    company: "Notion Labs",
    name: "Priya Raman",
    role: "recruiter",
    source: "careers_page",
    profileUrl: "https://linkedin.com/in/priya-raman-example",
    lastContactAt: null,
  },
  {
    id: "c2",
    company: "Notion Labs",
    name: "Dev Chandra",
    role: "engineer",
    source: "github",
    profileUrl: "https://github.com/devchandra-example",
    lastContactAt: null,
  },
  {
    id: "c3",
    company: "Anthropic",
    name: "Sam Whitfield",
    role: "hiring_manager",
    source: "public_directory",
    profileUrl: "https://linkedin.com/in/sam-whitfield-example",
    lastContactAt: "2026-07-20T10:05:00Z",
  },
];

export const MOCK_OUTREACH: OutreachMessage[] = [
  {
    id: "o1",
    contactId: "c1",
    contactName: "Priya Raman",
    company: "Notion Labs",
    variant: "referral",
    draft: "Hi Priya — I just applied for the Founding AI Engineer role. I've shipped a very similar RAG + multi-agent system in production (details in my application) and would love a referral if you think it's a fit. Happy to share more context.",
    status: "draft",
  },
  {
    id: "o2",
    contactId: "c2",
    contactName: "Dev Chandra",
    company: "Notion Labs",
    variant: "show_project",
    draft: "Hi Dev — saw you work on the AI platform team at Notion. I've been building something similar (MCP-orchestrated multi-agent system, RAG over pgvector) and would love to compare notes if you have 15 minutes sometime.",
    status: "draft",
  },
];

export const MOCK_FOLLOWUPS: FollowUp[] = [
  {
    id: "f1",
    applicationId: "a3",
    company: "Datadog",
    title: "Backend Engineer",
    recruiterEmail: "talent@datadog.com",
    dueAt: "2026-07-27T00:00:00Z",
    messageDraft: "Hi team — following up on my application for the Backend Engineer role submitted on July 18th. Still very interested and happy to answer any questions.",
    status: "pending",
  },
];

export const MOCK_REPLIES: EmailReply[] = [
  {
    id: "r1",
    company: "Anthropic",
    from: "recruiting@anthropic.com",
    subject: "Next steps — Applied AI Engineer",
    receivedAt: "2026-07-25T09:15:00Z",
    classification: "interview_invite",
    draftResponse: "Thank you so much for the update — I'd love to move forward. I'm available Tuesday-Thursday next week, mornings preferred. Let me know what works best for the team.",
    status: "pending_review",
  },
  {
    id: "r2",
    company: "Datadog",
    from: "talent@datadog.com",
    subject: "Update on your application",
    receivedAt: "2026-07-24T16:40:00Z",
    classification: "rejection",
    draftResponse: "Thank you for letting me know, and for considering my application. I'd welcome any feedback if you're able to share it, and hope to cross paths on a future opening.",
    status: "pending_review",
  },
  {
    id: "r3",
    company: "Palantir",
    from: "no-reply@greenhouse.io",
    subject: "Your online assessment for Machine Learning Engineer",
    receivedAt: "2026-07-27T13:00:00Z",
    classification: "assessment_invite",
    draftResponse: "Thank you for the invite — I'll complete the assessment within the stated window and will reach out if anything is unclear. Looking forward to it.",
    status: "pending_review",
  },
  {
    id: "r4",
    company: "Stripe",
    from: "no-reply@ashbyhq.com",
    subject: "We've received your application",
    receivedAt: "2026-07-27T08:05:00Z",
    classification: "confirmation",
    draftResponse: "",
    status: "approved",
  },
];

export const MOCK_REPORTS: DailyReport[] = [
  {
    date: "2026-07-26",
    applied: 6,
    skipped: 41,
    drafted: 6,
    followUpsDue: 1,
    statsByTrack: [
      { label: "AI Engineer track", applied: 2, replies: 1, replyRate: 0.5 },
      { label: "Software Engineer track", applied: 2, replies: 0, replyRate: 0 },
      { label: "Data Engineer track", applied: 2, replies: 1, replyRate: 0.5 },
    ],
    journalEntry:
      "Only 9 outcomes logged on the AI Engineer track so far — below the ~15-20 minimum sample, so no strategy change yet, running on defaults. Early signal: roles mentioning 'MCP' or 'multi-agent' explicitly are converting to replies faster than generic 'GenAI' postings. Watching this, not acting on it yet.",
  },
];

export const MOCK_STRATEGY_VERSIONS: StrategyProfileVersion[] = [
  {
    version: 1,
    createdAt: "2026-07-20T02:00:00Z",
    summary: "Baseline — defaults, no learned adjustments yet.",
    changes: ["Initial resume weighting: even across all 11 tracks", "Outreach tone: direct, evidence-led", "Follow-up timing: 6 business days"],
    sampleSize: 0,
    status: "approved",
  },
  {
    version: 2,
    createdAt: "2026-07-26T02:00:00Z",
    summary: "First tentative signal on AI Engineer track — still below min-sample, held for review, not auto-applied.",
    changes: ["Proposed: rank AI Engineer roles mentioning 'MCP' or 'multi-agent' 15% higher", "No change to outreach tone or follow-up timing (insufficient data)"],
    sampleSize: 9,
    status: "pending_review",
  },
];

export const MOCK_AUDIT_LOG: AuditLogEntry[] = [
  { id: "l1", actor: "scout", action: "scraped_batch", details: "127 jobs pulled for Day 1 (midsize) theme via Adzuna + Greenhouse boards.", createdAt: "2026-07-27T08:00:00Z" },
  { id: "l2", actor: "fit_scorer", action: "scored_job", details: "Stripe · AI Engineer, Platform → strong (0.88 ATS match)", createdAt: "2026-07-27T08:02:10Z" },
  { id: "l3", actor: "fit_scorer", action: "skipped_job", details: "US Dept of Commerce · Data Analyst (GS-9) → weak, citizenship requirement", createdAt: "2026-07-27T08:09:05Z" },
  { id: "l4", actor: "applier", action: "submitted_application", details: "Notion Labs · Founding AI Engineer — approved by human, submitted via portal", createdAt: "2026-07-26T14:32:00Z" },
  { id: "l5", actor: "reflection", action: "proposed_strategy_v2", details: "Held for human review — sample size 9, below min threshold of 15-20", createdAt: "2026-07-27T02:00:00Z" },
];
