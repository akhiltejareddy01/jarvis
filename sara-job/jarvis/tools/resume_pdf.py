"""Renders a structured resume (see SCHEMA below) into a PDF matching the
visual template of Akhil's real resumes — serif font, dark-blue section
headers with a full-width rule, company/dates on one line and role/location
on the next. Verified by rendering resumes/Ai_Engineer_...pdf to an image and
matching layout/colors against it directly, not guessed.

Uses Playwright (headless Chromium print-to-PDF) rather than reportlab/
weasyprint — it's already a planned dependency for the Applier step, and CSS
gives far more reliable control over this layout than manual PDF positioning.

SCHEMA (also see ResumeVariant.structured / the *_PROMPT in resume_selector.py):
{
  "name": str, "tagline": str, "location": str, "phone": str, "email": str,
  "linkedin": str, "github": str, "summary": str,
  "experience": [{"company","dates","role","location","description","bullets":[...]}],
  "projects": [{"name","tags","bullets":[...]}],
  "skills": [{"category","items"}],
  "certifications": [str], "publications": [str],
  "education": [{"institution","dates","degree","location"}]
}
"""

import html
import os
from pathlib import Path

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH", str(Path(__file__).resolve().parent.parent.parent / ".cache" / "ms-playwright")
)

from playwright.sync_api import sync_playwright

CSS = """
@page { size: Letter; margin: 0; }
body { font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; font-size: 10.3pt; line-height: 1.35; }
.header h1 { font-size: 24pt; margin: 0; }
.tagline { color: #1f4e79; font-size: 12pt; margin: 2px 0 6px; }
.contact { font-size: 9.5pt; margin-bottom: 4px; }
.contact a { color: #1a5eb8; text-decoration: underline; }
hr { border: none; border-top: 0.75pt solid #888; margin: 4px 0 10px; }
h2 { color: #1f4e79; font-size: 13pt; border-bottom: 0.75pt solid #888; padding-bottom: 2px; margin: 14px 0 6px; }
.row { display: flex; justify-content: space-between; }
.bold { font-weight: bold; }
.italic { font-style: italic; }
.desc { font-style: italic; color: #555; margin: 1px 0 3px; }
ul { margin: 2px 0 8px; padding-left: 18px; }
li { margin-bottom: 2px; }
.entry { margin-bottom: 8px; }
"""


def _esc(s: str) -> str:
    return html.escape(s or "")


def _entry_row(left: str, right: str, cls: str = "") -> str:
    return f'<div class="row {cls}"><span>{_esc(left)}</span><span>{_esc(right)}</span></div>'


def _bullets(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_esc(b)}</li>" for b in items) + "</ul>" if items else ""


def render_html(r: dict) -> str:
    contact_parts = [p for p in [r.get("location"), r.get("phone"), r.get("email")] if p]
    contact = " | ".join(_esc(p) for p in contact_parts)
    links = []
    if r.get("linkedin"):
        links.append(f'<a href="https://{_esc(r["linkedin"])}">{_esc(r["linkedin"])}</a>')
    if r.get("github"):
        links.append(f'<a href="https://{_esc(r["github"])}">{_esc(r["github"])}</a>')
    if links:
        contact += " | " + " | ".join(links)

    experience_html = "".join(
        f'<div class="entry">'
        f'{_entry_row(e.get("company", ""), e.get("dates", ""), "bold")}'
        f'{_entry_row(e.get("role", ""), e.get("location", ""), "italic")}'
        + (f'<div class="desc">{_esc(e.get("description", ""))}</div>' if e.get("description") else "")
        + _bullets(e.get("bullets", []))
        + "</div>"
        for e in r.get("experience", [])
    )

    projects_html = "".join(
        f'<div class="entry">{_entry_row(p.get("name", ""), p.get("tags", ""), "bold")}{_bullets(p.get("bullets", []))}</div>'
        for p in r.get("projects", [])
    )

    skills_html = "".join(
        f'<div><span class="bold">{_esc(s.get("category", ""))}:</span> {_esc(s.get("items", ""))}</div>'
        for s in r.get("skills", [])
    )

    education_html = "".join(
        f'<div class="entry">'
        f'{_entry_row(ed.get("institution", ""), ed.get("dates", ""), "bold")}'
        f'{_entry_row(ed.get("degree", ""), ed.get("location", ""), "italic")}'
        "</div>"
        for ed in r.get("education", [])
    )

    def section(title: str, body: str) -> str:
        return f"<h2>{_esc(title)}</h2>{body}" if body else ""

    certifications_html = _bullets(r.get("certifications", []))
    publications_html = "<ul>" + "".join(f"<li><i>{_esc(p)}</i></li>" for p in r.get("publications", [])) + "</ul>" if r.get("publications") else ""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="header">
  <h1>{_esc(r.get("name", ""))}</h1>
  <div class="tagline">{_esc(r.get("tagline", ""))}</div>
  <div class="contact">{contact}</div>
  <hr>
</div>
{section("Summary", f"<p>{_esc(r.get('summary', ''))}</p>")}
{section("Experience", experience_html)}
{section("Projects", projects_html)}
{section("Skills", skills_html)}
{section("Certifications", certifications_html)}
{section("Publications", publications_html)}
{section("Education", education_html)}
</body></html>"""


def render_pdf(structured: dict, out_path: str) -> str:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    html_content = render_html(structured)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(
            path=out_path,
            format="Letter",
            margin={"top": "0.55in", "bottom": "0.55in", "left": "0.75in", "right": "0.75in"},
            print_background=True,
        )
        browser.close()
    return out_path
