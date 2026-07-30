# Project JARVIS

**A personal, agentic career & life operating system — built in the open, one phase at a time.**

> 🚧 **Status: active development, not finished.** The first agent — **Sara Job** — is running end-to-end for the automated-fill part of the pipeline, with a human approving every ranked job before submission.

---

TL;DR: Agentic system that automates job discovery, fit scoring, and one-click assisted application submissions while keeping a human-in-the-loop for approvals.

## What this is

JARVIS coordinates job search, outreach, and tracking as cooperating agents rather than manual processes. It's intended for job seekers who want automation with strong auditability and human oversight.

## Quick facts
- Tech: Python, FastAPI, LangGraph, SQLAlchemy, Postgres + pgvector, Playwright, Next.js
- Status: Active development (Sara Job phase)
- Contact: yvakhilteja1104@gmail.com

## How to run (short)

Backend:

```bash
cd sara-job
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn jarvis.api.main:app --reload --port 8000
```

Frontend:

```bash
cd sara-job/web
npm install
npm run dev
```

Both need `.env` files (not checked in) with database and LLM provider credentials.

## Highlights
- Database schema and early agent pipeline (scout → parser → scorer → selector → applier) are implemented.
- Playwright-based applier fills applications in a visible browser for human final approval.

## Contributing
Open issues or PRs. See ISSUE_TEMPLATE.md and PULL_REQUEST_TEMPLATE.md for guidance.

## License
This project is licensed under the MIT License — see LICENSE
