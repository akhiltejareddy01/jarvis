"""Job source clients — per Sara_Job_Arch.docx §"Frozen decisions":
"No LinkedIn scraping. Job APIs only... Adzuna + USAJobs + curated Greenhouse /
Lever / Ashby boards." Every endpoint/field here was verified live against the
real APIs on 2026-07-27, not guessed from docs.

Every fetch_* function returns a list of normalized dicts:
    {source, external_id, title, company_name, location, remote, url, jd_text}
so agents/scout.py doesn't need to know which API a job came from.
"""

import html
import re
from pathlib import Path

import httpx
import yaml

from jarvis.config import settings

BOARDS_PATH = Path(__file__).resolve().parent.parent / "config" / "boards.yaml"


def _strip_html(raw: str) -> str:
    # Greenhouse (and others) return content as HTML-entity-escaped HTML
    # (e.g. "&lt;h2&gt;") — unescape BEFORE stripping tags, or the tag regex
    # never matches anything and you get literal "<h2>" in the output.
    unescaped = html.unescape(raw or "")
    return re.sub(r"<[^<]+?>", " ", unescaped).strip()


def _load_boards() -> dict:
    with open(BOARDS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_adzuna(query: str, location: str = "", pages: int = 1) -> list[dict]:
    jobs = []
    for page in range(1, pages + 1):
        params = {
            "app_id": settings.adzuna_app_id,
            "app_key": settings.adzuna_app_key,
            "results_per_page": 20,
            "what": query,
            "content-type": "application/json",
        }
        if location:
            params["where"] = location
        resp = httpx.get(
            f"https://api.adzuna.com/v1/api/jobs/us/search/{page}", params=params, timeout=20
        )
        resp.raise_for_status()
        for r in resp.json().get("results", []):
            jobs.append({
                "source": "adzuna",
                "external_id": str(r["id"]),
                "title": r.get("title", ""),
                "company_name": r.get("company", {}).get("display_name", ""),
                "company_category": "",  # Adzuna doesn't tell us company size/type — don't guess
                "location": r.get("location", {}).get("display_name", ""),
                "remote": "remote" in (r.get("title", "") + r.get("description", "")).lower(),
                "url": r.get("redirect_url", ""),
                "jd_text": r.get("description", ""),
            })
    return jobs


def fetch_usajobs(query: str, location: str = "") -> list[dict]:
    params = {"Keyword": query, "ResultsPerPage": 25}
    if location:
        params["LocationName"] = location
    resp = httpx.get(
        "https://data.usajobs.gov/api/search",
        params=params,
        headers={
            "Host": "data.usajobs.gov",
            "User-Agent": "yvakhilteja2003@gmail.com",
            "Authorization-Key": settings.usajobs_api_key,
        },
        timeout=20,
    )
    resp.raise_for_status()
    jobs = []
    for item in resp.json().get("SearchResult", {}).get("SearchResultItems", []):
        d = item["MatchedObjectDescriptor"]
        jobs.append({
            "source": "usajobs",
            "external_id": str(item["MatchedObjectId"]),
            "title": d.get("PositionTitle", ""),
            "company_name": d.get("OrganizationName", ""),
            "company_category": "gov",  # USAJobs is exclusively US government listings — this is a fact, not a guess
            "location": d.get("PositionLocationDisplay", ""),
            "remote": False,
            "url": d.get("PositionURI", ""),
            "jd_text": d.get("UserArea", {}).get("Details", {}).get("JobSummary", ""),
        })
    return jobs


def fetch_greenhouse_board(slug: str) -> list[dict]:
    resp = httpx.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true", timeout=20)
    resp.raise_for_status()
    jobs = []
    for j in resp.json().get("jobs", []):
        jobs.append({
            "source": "greenhouse",
            "external_id": str(j["id"]),
            "title": j.get("title", ""),
            "company_name": j.get("company_name", slug),
            "location": (j.get("location") or {}).get("name", ""),
            "remote": "remote" in ((j.get("location") or {}).get("name", "")).lower(),
            "url": j.get("absolute_url", ""),
            "jd_text": _strip_html(j.get("content", "")),
        })
    return jobs


def fetch_lever_board(slug: str) -> list[dict]:
    resp = httpx.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", timeout=20)
    resp.raise_for_status()
    jobs = []
    for j in resp.json():
        categories = j.get("categories", {})
        jobs.append({
            "source": "lever",
            "external_id": str(j["id"]),
            "title": j.get("text", ""),
            "company_name": slug,
            "location": categories.get("location", ""),
            "remote": "remote" in (categories.get("location", "") or "").lower(),
            "url": j.get("hostedUrl", ""),
            "jd_text": j.get("descriptionPlain", "") or _strip_html(j.get("description", "")),
        })
    return jobs


def fetch_ashby_board(slug: str) -> list[dict]:
    resp = httpx.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}", timeout=20)
    resp.raise_for_status()
    jobs = []
    for j in resp.json().get("jobs", []):
        location = j.get("location", "") or j.get("locationName", "")
        jobs.append({
            "source": "ashby",
            "external_id": str(j["id"]),
            "title": j.get("title", ""),
            "company_name": slug,
            "location": location,
            "remote": bool(j.get("isRemote")) or "remote" in (location or "").lower(),
            "url": j.get("jobUrl", "") or j.get("applyUrl", ""),
            "jd_text": j.get("descriptionPlain", "") or _strip_html(j.get("descriptionHtml", "")),
        })
    return jobs


def fetch_curated_boards(category: str | None = None) -> list[dict]:
    """Pull every job from every curated board, optionally filtered to boards
    tagged with `category` (midsize/university/gov/mnc/startup — today's theme).
    These are companies Akhil specifically wants to watch, not keyword-filtered."""
    boards = _load_boards()
    fetchers = {
        "greenhouse": fetch_greenhouse_board,
        "lever": fetch_lever_board,
        "ashby": fetch_ashby_board,
    }
    jobs = []
    for ats, fetcher in fetchers.items():
        for slug, cat in boards.get(ats, {}).items():
            if category and cat != category:
                continue
            board_jobs = fetcher(slug)
            for j in board_jobs:
                j["company_category"] = cat  # known for real, from boards.yaml
            jobs.extend(board_jobs)
    return jobs
