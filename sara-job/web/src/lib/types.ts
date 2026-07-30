// Local shapes for the frontend-only phase. These mirror the tables the locked
// architecture doc defines (profile info feeds resume_variants/contacts-adjacent
// data; DailyIntake matches the `daily_intake` table exactly) so swapping
// localStorage for real API calls later is a straight lift, not a redesign.

export type ScreeningAnswer = {
  question: string;
  answer: string;
};

export type ResumeVariant = {
  track: string; // e.g. "Backend", "Data", "AI/ML"
  fileName: string; // actual upload wiring comes with the backend
  notes: string;
};

export type Profile = {
  fullName: string;
  email: string;
  phone: string;
  linkedinUrl: string;
  githubUrl: string;
  portfolioUrl: string;

  targetRoles: string[]; // e.g. ["Backend Engineer", "Data Engineer"]
  experienceYears: number;
  locations: string[];
  remoteOk: boolean;
  salaryMin: number;
  salaryMax: number;

  workAuthorization: string; // e.g. "US Citizen", "H1B", "OPT/CPT", "Need Sponsorship"
  noticePeriod: string; // e.g. "Immediate", "2 weeks", "1 month"

  resumes: ResumeVariant[];
  screeningAnswers: ScreeningAnswer[];

  // EEO — optional, self-identification only, defaults to "Decline to answer"
  eeoGender: string;
  eeoRace: string;
  eeoVeteranStatus: string;
  eeoDisabilityStatus: string;

  updatedAt: string;
};

export const EMPTY_PROFILE: Profile = {
  fullName: "",
  email: "",
  phone: "",
  linkedinUrl: "",
  githubUrl: "",
  portfolioUrl: "",
  targetRoles: [],
  experienceYears: 0,
  locations: [],
  remoteOk: true,
  salaryMin: 0,
  salaryMax: 0,
  workAuthorization: "US Citizen",
  noticePeriod: "Immediate",
  resumes: [],
  screeningAnswers: [],
  eeoGender: "Decline to answer",
  eeoRace: "Decline to answer",
  eeoVeteranStatus: "Decline to answer",
  eeoDisabilityStatus: "Decline to answer",
  updatedAt: "",
};

export type DailyIntake = {
  runDate: string; // YYYY-MM-DD
  track: string;
  locations: string[];
  remoteOk: boolean;
  salaryFloor: number;
  targetCount: number;
  mode: "semi_auto" | "auto";
  focusCompanies: string[];
  avoidCompanies: string[];
  status: "pending" | "started" | "paused" | "done";
};

export function dailyIntakeFromProfile(profile: Profile, runDate: string): DailyIntake {
  return {
    runDate,
    track: profile.targetRoles[0] ?? "",
    locations: profile.locations,
    remoteOk: profile.remoteOk,
    salaryFloor: profile.salaryMin,
    targetCount: 50,
    mode: "semi_auto",
    focusCompanies: [],
    avoidCompanies: [],
    status: "pending",
  };
}

// ============================================================
// Everything below mirrors a table from the locked architecture doc
// (Sara_Job_Arch.docx §"Database tables"). Jobs come from the real backend
// (see lib/api.ts) as of 2026-07-27; everything else here is still
// mock/sample data until its agent gets built — see mockData.ts.
// ============================================================

export type FitRating = "strong" | "medium" | "weak";

export type Job = {
  id: string;
  company: string;
  companyCategory: string; // "" = unknown (e.g. Adzuna doesn't expose company size)
  title: string;
  location: string;
  remote: boolean;
  url: string;
  themeDay: string;
  fitRating: FitRating | null;
  fitReason: string | null;
  resumeUsed: string | null; // null until Resume Selector is built
  atsScore: number | null; // null until Resume Selector is built
  coverLetterPreview: string | null; // null until Cover Letter agent is built
  status: "new" | "approved" | "skipped" | "applied";
  seenAt: string;
};

export type Application = {
  id: string;
  jobId: string;
  company: string;
  title: string;
  jobUrl: string;
  resumeVariant: string;
  submittedVia: string; // the ATS the Applier used, e.g. "ashby" — not just portal/email/linkedin
  status: string; // draft | submitted | ...
  proofScreenshotUrl: string | null; // relative API path, e.g. "/api/applications/{id}/screenshot"
  submittedAt: string | null;
  lastEventAt: string;
};

export type Contact = {
  id: string;
  company: string;
  name: string;
  role: "recruiter" | "hiring_manager" | "engineer" | "alumni";
  source: "careers_page" | "github" | "public_directory";
  profileUrl: string;
  lastContactAt: string | null;
};

export type OutreachMessage = {
  id: string;
  contactId: string;
  contactName: string;
  company: string;
  variant: "referral" | "info_chat" | "show_project";
  draft: string;
  status: "draft" | "sent" | "skipped";
};

export type FollowUp = {
  id: string;
  applicationId: string;
  company: string;
  title: string;
  recruiterEmail: string; // "to" address for the drafted nudge
  dueAt: string;
  messageDraft: string;
  status: "pending" | "sent" | "skipped";
};

export type ReplyClassification =
  | "confirmation" // automated "we received your application" — logged only, no draft
  | "assessment_invite"
  | "interview_invite"
  | "offer"
  | "rejection"
  | "info_request"
  | "other";

export type EmailReply = {
  id: string;
  company: string;
  from: string;
  subject: string;
  receivedAt: string;
  classification: ReplyClassification;
  draftResponse: string; // sits in Gmail Drafts via email-agent — never auto-sent
  status: "pending_review" | "approved" | "skipped";
};

export type DailyReportStat = {
  label: string; // e.g. "Backend track", "MNC/big-tech companies"
  applied: number;
  replies: number;
  replyRate: number; // 0-1
};

export type DailyReport = {
  date: string;
  applied: number;
  skipped: number;
  drafted: number;
  followUpsDue: number;
  statsByTrack: DailyReportStat[];
  journalEntry: string; // human-readable reflection, numbers-led
};

export type StrategyProfileVersion = {
  version: number;
  createdAt: string;
  summary: string;
  changes: string[]; // bounded action space only: resume weights, tone, track priority, follow-up timing
  sampleSize: number;
  status: "pending_review" | "approved" | "rejected" | "rolled_back";
};

export type AuditLogEntry = {
  id: string;
  actor: string; // agent name
  action: string;
  details: string;
  createdAt: string;
};
