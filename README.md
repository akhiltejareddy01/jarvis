# Project JARVIS

**A personal, agentic career & life operating system — built in the open, one phase at a time.**

> 🚧 **Status: active development, not finished.** The first agent — **Sara Job** — is running end-to-end for the automated-fill part of the pipeline, with a human approving every ranked job and clicking the final Submit. Everything below is a real, current snapshot, not a plan written in advance of the code.

---

## What this is

JARVIS is designed to run a person's job search, professional network, and eventually side-projects and personal logistics, as a set of cooperating agents instead of a pile of manual tabs and spreadsheets. It's built with two faces sharing one codebase:

- **Private Operator** — runs on real accounts and real data, fully agentic with a human approval gate before anything irreversible happens.
- **Public Stage** — a portfolio-site demo of the same system running on synthetic data, so the build itself can be shown to recruiters/collaborators without exposing anything private.

The full vision spans job search, professional connections, a startup-idea engine, freelance work, and general life-ops. The current build effort is entirely focused on the first slice: **Sara Job**, the job-application agent.

## Architecture at a glance

```
Scheduler (daily, theme-of-the-day)
   → Scout            scrape 100–150 jobs/day (Adzuna, USAJobs, curated Greenhouse/Lever/Ashby)
   → Dedup             pgvector similarity against past jobs
   → JD Parser         → structured fields (skills, seniority, location, remote)
   → Fit Scorer        Strong / Medium / Weak + one-line reason, filters out Weak
   → Resume Selector   best-of-7 resumes if one clears the bar, else Claude tailors a rewrite
   → Cover Letter      Claude drafts the "why me"
   → Dashboard         ranked list, one-tap Approve / Skip
   → Applier           on approve: fills the real application in a visible browser,
                        human clicks the final Submit
   → Log               company + proof screenshot saved
   → Email layer        (not yet built) watch inbox, classify replies, follow-up timers
   → Reflection         (not yet built) nightly: stats → Strategy Profile → journal
```

Everything goes through a FastAPI REST layer — the Next.js frontend never touches agents or the database directly.

### The "brain" (designed, not yet built)
Three planned layers sit above the pipeline once enough outcome data exists:
1. **Memory** — every job/application/outcome embedded in pgvector and retrievable (recall, not learning).
2. **Reflection** — a nightly stats-first pass (reply rates by track/company/resume) that turns numbers into a versioned strategy, never the other way around.
3. **Strategy Profile** — a versioned JSON playbook injected into every agent prompt the next day, plus a human-readable journal entry.

Guardrails that apply regardless of how "smart" the brain gets: bounded action space (it can only re-rank/re-word, never invent new actions), an honesty lock (tailoring may reframe, never fabricate experience), no auto-submit ever, fixed per-site rate caps, minimum-sample thresholds before trusting a pattern, human veto on every strategy change, and a full audit log with a kill switch.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python, FastAPI, LangGraph, SQLAlchemy 2.0 |
| Database | Postgres + pgvector (Supabase) |
| Bulk LLM | Groq free tier (Llama 3.3 70B) — parsing, scoring, drafting |
| Premium LLM | Claude — resume rewrites, final human-facing text |
| Embeddings | local sentence-transformers (nomic/bge, 768-dim) |
| Browser automation | Playwright, human-in-the-loop submit |
| Job sources | Adzuna, USAJobs, Greenhouse/Lever/Ashby APIs — no LinkedIn scraping, ever |
| Frontend | Next.js 16 (App Router) + Tailwind |

## What's actually built so far

- **Database schema** (`sara-job/jarvis/db/models.py`) — 11 tables live: profile facts, resume variants, screening answers, daily intake, companies, jobs (+ embeddings), applications, contacts, daily reports, and an action log.
- **Scout** (`agents/scout.py` + `tools/job_sources.py`) — pulls from Adzuna, USAJobs, and curated ATS boards on a Mon–Fri weekly theme (midsize / university / gov / MNC / startup), with hard dedup on source+ID and soft dedup via embedding similarity.
- **JD Parser → Fit Scorer → Resume Selector → Cover Letter**, wired as a real LangGraph state graph (`agents/graph.py`), not just scripts called in sequence.
- **Resume Selector** — scores the existing 7 resumes against each JD; falls back to a Claude-tailored rewrite (honesty-locked: reframe/re-emphasize only, never fabricate) when none clears the bar.
- **Applier** (`agents/applier.py`) — Playwright automation for Ashby-hosted applications. Fills every field (contact info, resume upload, honest LLM-drafted answers) in a real, visible browser window, then **stops and hands off to the human for the final Submit click** — a deliberate, tested decision, not a shortcut: an earlier version that auto-clicked Submit got silently flagged as spam by Ashby's bot detection despite returning HTTP 200. It will not attempt to solve a CAPTCHA under any circumstance.
- **FastAPI REST layer** (`api/main.py`) — `/api/jobs`, `/api/applications`, approve/skip, open-application-in-browser, and human confirm/reject-submission endpoints.
- **Next.js dashboard** (`web/`) — working pages for jobs, applications, contacts, follow-ups, profile, replies, reports, strategy, and an audit log view.
- **Real Gmail deep-link handoff** — drafted outreach/replies open directly in Gmail's own compose UI for a human to review and send (not yet wired to read/classify incoming mail).

## What's not built yet

- **Scheduler** — the daily automated trigger doesn't exist yet; the pipeline currently runs on demand.
- **Email integration** — no inbox reading, reply classification, or 5–7 business-day follow-up timers yet. Only the outbound Gmail-compose deep link exists today.
- **Reflection + Strategy Profile + journal** — the "brain" described above is fully designed in the architecture doc but has no code yet. No strategy versioning, no nightly stats pass.
- **Additional ATS handlers** — Applier only supports Ashby today; Greenhouse and Lever are planned, Workday is planned to stay manual by design.
- **Connection-finder / outreach / supervisor agents** — named in the architecture but not started.
- **Guardrail hardening** — the audit log table and dashboard view exist; the kill switch and enforced per-site rate/volume caps are not yet implemented.
- **Public Stage demo** — the synthetic-data portfolio view (with PII redaction) hasn't been built; today there's only a private, real-data dashboard.

## Repo layout

```
JARVIS/
  JARVIS.pdf                 original full-system feature spec
  JARVIS_Architecture.pdf    one-page system architecture diagram
  JARVIS_Plan.pdf            original build spec v0.1 (superseded in places, see below)
  sara-job/                  the only phase under active build right now
    Sara_Job_Arch.docx       locked, current source of truth for this phase
    jarvis/
      config.py              settings from .env
      db/                    session.py, models.py
      core/                  llm.py, embeddings.py
      agents/                scout, jd_parser, fit_scorer, resume_selector,
                              cover_letter, applier
      tools/                 job_sources.py, resume_pdf.py
      api/                   FastAPI routes
    scripts/                 init_db.py, seed_profile.py
    web/                     Next.js dashboard
```

Two docs intentionally disagree in places (e.g. Telegram vs. website as the interface) — **`Sara_Job_Arch.docx` is the locked, authoritative doc for the current phase**; the PDFs are the original wider-scope vision this phase grew out of.

## Running it locally

```bash
# backend
cd sara-job
py -3.11 -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn jarvis.api.main:app --reload --port 8000

# frontend
cd sara-job/web
npm install
npm run dev
```

Both need their own `.env` / `.env.local` (gitignored, not included here) with database and API-provider credentials.

---

*No LinkedIn scraping. No auto-submit. No fabricated experience. Human approves every application before it goes out.*
