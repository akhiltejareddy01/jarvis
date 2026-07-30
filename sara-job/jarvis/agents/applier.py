"""Applier — per Sara_Job_Arch.docx §"Frozen decisions": "Apply mode: semi-auto.
Sara prepares everything; you approve on the website; browser-use submits.
Greenhouse/Lever/Ashby automated first; Workday manual at first."

Only Ashby is implemented so far — it's the only ATS actually represented in
Akhil's current approved queue, and its application form has a clean, stable
DOM pattern (`.ashby-application-form-field-entry` divs each containing a
proper `<label for>` + input) verified by hand against a real posting rather
than guessed. Extend ATS_HANDLERS with greenhouse/lever functions once a real
job on those boards needs it — don't build them blind.

Hard safety line, not a preference: this will NOT solve or click through a
CAPTCHA challenge under any circumstances.

This does NOT click Submit, ever — an earlier version did, and a real test
against a real Linear posting on 2026-07-27 got rejected server-side with
"Your application submission was flagged as possible spam" (Ashby runs
SEON-style bot/device fingerprinting, visible in its network traffic). The
HTTP response to the submit GraphQL call was still a 200 — GraphQL APIs
return 200 on the transport layer even when the operation itself failed, so
checking status codes alone produced a false "submitted" the first time this
ran. That's a real, structural problem with automating the final click on a
platform actively trying to detect automation, not a bug worth patching around.

So: this fills every field (contact info, resume upload, honest LLM-drafted
answers to open-ended questions) in a REAL VISIBLE (non-headless) Chromium
window and leaves it open and idle for a human to review and click Submit
themselves. That one click, coming from a real interactive human session
instead of a synthetic automated one, is exactly what the anti-bot check is
designed to require.
"""

import json
import os
import uuid
from pathlib import Path

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH", str(Path(__file__).resolve().parent.parent.parent / ".cache" / "ms-playwright")
)

from playwright.sync_api import sync_playwright
from sqlalchemy import select

from jarvis.core.llm import ask_premium
from jarvis.db.models import Application, Job, ProfileFact, ScreeningAnswer
from jarvis.db.session import get_session

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent.parent / "application_screenshots"

ANSWER_PROMPT = """Answer this job application question, grounded ONLY in the candidate's real resume and stated preferences below. Be specific and honest — reference real experience or preferences where relevant. Do NOT invent any skill, employer, project, achievement, or preference not present in the source material below. If the question is about a logistics/preference fact (location, remote, salary, notice period) and the stated preferences answer it, use that directly rather than deflecting.

Question: {question}
{description}

Candidate's stated preferences:
{profile_summary}

Candidate's resume:
{resume_text}

Reply with ONLY the answer text, no preamble, no restating the question. Keep it appropriately concise for a job application field (a few sentences, not an essay), unless the question explicitly asks for more.
"""

YESNO_PROMPT = """A job application asks this Yes/No question. Answer using ONLY the candidate's stated preferences below — do not guess beyond what's stated. Reply with ONLY the single word "Yes" or "No".

Question: {question}

Candidate's stated preferences:
{profile_summary}
"""


def _profile_value(session, category: str, key: str, default: str = "") -> str:
    fact = session.scalar(
        select(ProfileFact).where(ProfileFact.category == category, ProfileFact.key == key)
    )
    return fact.value if fact else default


def _screening_answer(session, question_key: str, default: str = "") -> str:
    answer = session.scalar(select(ScreeningAnswer).where(ScreeningAnswer.question_key == question_key))
    return answer.answer if answer else default


def _profile_summary(session) -> str:
    fields = [
        ("Locations willing to work from", "preferences", "locations"),
        ("Open to fully remote", "preferences", "remote_ok"),
        ("Years of experience", "preferences", "experience_years"),
        ("Desired salary range", "compensation", None),
        ("Notice period", "work_auth", "notice_period"),
        ("Work authorization", "work_auth", "status"),
    ]
    lines = []
    for label, category, key in fields:
        if key:
            value = _profile_value(session, category, key)
        else:
            lo, hi = _profile_value(session, category, "salary_min"), _profile_value(session, category, "salary_max")
            value = f"${lo}-${hi}" if lo and hi else ""
        if value:
            lines.append(f"- {label}: {value}")
    return "\n".join(lines)


EEO_DECLINE = "Decline to answer"


def _match_known_field(question: str, session) -> str | None:
    """Returns a value for fields we can answer deterministically from the
    Profile Brain, or None if this needs an LLM-drafted or manual answer.

    Only fires on SHORT questions (real field labels like "Email" or
    "LinkedIn Profile") — a real run answered "How would you prioritize and
    share user feedback... (email, Slack, and X)..." with Akhil's email
    address, because that whole sentence contains the substring "email" and
    the old code matched on substring alone with no length check. A field
    label and a sentence that happens to mention a keyword are not the same
    thing; only the former should ever hit these shortcuts."""
    if len(question) > 60:
        return None

    q = question.lower()
    # Checked before the generic "name" catch-all below — Greenhouse splits
    # name into separate First/Last/Preferred fields, and a real run answered
    # all three with the FULL name because "name" matches all of them equally
    # with no way to tell which is which. Order matters: "first" must be
    # checked before "preferred", since "preferred first name" contains both.
    if "last name" in q or "surname" in q or "family name" in q:
        return _profile_value(session, "contact", "last_name")
    if "preferred" in q and "name" in q:
        return _profile_value(session, "contact", "first_name")  # goes by given name day to day
    if "first name" in q or "given name" in q:
        return _profile_value(session, "contact", "first_name")
    if "name" in q:
        return _profile_value(session, "contact", "full_name")
    if "email" in q:
        return _profile_value(session, "contact", "email")
    if "phone" in q:
        return _profile_value(session, "contact", "phone")
    if "linkedin" in q:
        return _profile_value(session, "contact", "linkedin_url")
    if "github" in q:
        return _profile_value(session, "contact", "github_url")  # deliberately blank — no placeholder
    if "twitter" in q or "x.com" in q or "portfolio" in q:
        return ""  # not something Akhil has — leave blank rather than guess
    if "notice" in q and "period" in q:
        return _screening_answer(session, "notice_period", "Immediate")
    if "sponsor" in q:
        return _screening_answer(session, "visa_sponsorship")
    if "authoriz" in q and "work" in q:
        return _screening_answer(session, "work_authorization")
    if "salary" in q or "compensation" in q:
        return _screening_answer(session, "desired_salary")
    if "country" in q and "based" in q:
        return "United States"
    if any(kw in q for kw in ("gender", "pronoun", "race", "ethnic", "hispanic", "latino", "disab", "veteran", "lgbtq", "sexual orientation")):
        return EEO_DECLINE  # EEO self-ID questions — matches the "Decline to answer" default set on the Profile page
    return None


def _match_yesno_field(question: str, session, stored_answers: dict | None = None) -> str:
    """Yes/No button-pair widgets (Ashby renders these as two <button>
    elements over a hidden checkbox, not a real HTML radio/checkbox you can
    just leave at a sane default — a real test run left one of these
    completely unanswered because the original field-scan only looked for
    <input>/<textarea>/<select> and missed button-based controls entirely).

    Falls back to an LLM call grounded in the Profile Brain's stated
    preferences for anything not covered by the fast keyword checks below —
    a real run needed a yes/no answer to "This role is based in our Denver
    office 4x/week — does this align with your expectations?", which no
    fixed keyword list will ever fully anticipate. Every real application
    question deserves an actual honest answer, not a shrug.

    stored_answers reuses a previous run's answer for this exact question
    (see `reopen_application`) instead of re-calling the LLM — the answer to
    "does Denver in-office work for you" doesn't change between the prep
    pass and the moment you actually click the link, so there's no reason to
    pay for or wait on a second LLM call."""
    if stored_answers and question in stored_answers and stored_answers[question] in ("Yes", "No"):
        return stored_answers[question]

    q = question.lower()
    if "timezone" in q and ("us" in q or "eu" in q):
        return "Yes"  # Akhil is NY-based — satisfies a US-or-EU timezone requirement
    if "authoriz" in q and "work" in q:
        return "Yes"
    if "sponsor" in q:
        return "No"

    raw = ask_premium(YESNO_PROMPT.format(question=question, profile_summary=_profile_summary(session))).strip()
    return "Yes" if raw.lower().startswith("yes") else "No"


_DECLINE_SYNONYMS = ("decline", "prefer not", "don't wish", "do not wish", "not to answer", "not want to answer", "no answer")


def _select_dropdown_option(page, scope, wanted: str) -> tuple[bool, str]:
    """For a real native <select>, or a custom combobox-with-listbox (react-select
    and similar libraries, used by both Ashby's location field and Greenhouse's
    Country/custom-question/EEO fields — none of Greenhouse's EEO dropdowns
    turned out to be real <select> elements despite looking like one) — picks
    whichever visible option best matches `wanted`. Returns (matched, actual
    selected text) — never the wanted text, and never a guess: an earlier
    version fell back to clicking whatever option was first when nothing
    matched, which silently selected "Male" for a Gender field and "Yes, I
    have a disability, or have had one in the past" for Disability Status,
    because "Decline to answer" doesn't literally substring-match either
    field's real wording ("Decline To Self Identify" / "I do not want to
    answer"). For a field this sensitive, guessing is worse than leaving it
    for a human — this only ever clicks an option it's actually confident in.
    `scope` can be either the field's container OR the select/combobox
    element itself — checked directly rather than assumed, since callers
    scope fields differently depending on the ATS (Ashby has no id on some
    comboboxes so must pass a container; Greenhouse ids everything so passes
    the element)."""

    def matches(text: str) -> bool:
        t, w = text.lower(), wanted.lower()
        if t in w or w in t:
            return True
        if w == EEO_DECLINE.lower() and any(kw in t for kw in _DECLINE_SYNONYMS):
            return True
        return False

    is_self_select = scope.evaluate("el => el.tagName === 'SELECT'")
    select_el = scope if is_self_select else scope.locator("select")
    if is_self_select or select_el.count() > 0:
        options = select_el.locator("option").all_text_contents()
        match = next((o for o in options if matches(o)), None)
        if match:
            select_el.select_option(label=match)
            return True, match
        return False, ""

    # Combobox — two distinct widget behaviors exist and look identical until
    # you interact with them: autocomplete fields (Ashby's Location, this ATS's
    # Country) need typed text before any options render; plain option-list
    # comboboxes (Yes/No questions, EEO selects) show their full list on click
    # alone, and typing into them does nothing (a real run left every single
    # one of these unanswered because it always typed first and never checked
    # whether options were already showing). Try click-only first since it's
    # non-destructive either way, then fall back to typing.
    is_self_combo = scope.evaluate("el => el.getAttribute('role') === 'combobox'")
    combo = scope if is_self_combo else scope.locator('input[role="combobox"]')
    if not is_self_combo and combo.count() == 0:
        return False, ""
    combo.click()
    page.wait_for_timeout(500)
    # Scoped to :visible — a real run matched a completely unrelated, hidden
    # dropdown (an embedded phone-country-dial-code picker library sharing
    # role="option" on its collapsed list items) because this search was
    # page-wide with no visibility filter. Only the listbox actually opened
    # by the click above should ever be visible at this point.
    options = page.locator('[role="option"]:visible')
    if options.count() == 0:
        combo.type(wanted, delay=30)
        page.wait_for_timeout(1200)
        options = page.locator('[role="option"]:visible')
    count = options.count()
    for i in range(count):
        text = options.nth(i).text_content() or ""
        if matches(text):
            options.nth(i).click()
            return True, text
    if count > 0:
        page.keyboard.press("Escape")  # close the dropdown we opened rather than leave it hanging
    return False, ""


def _fill_ashby_form(page, job: Job, session, stored_answers: dict | None = None) -> dict:
    """stored_answers, when given (see `reopen_application`), skips every LLM
    call for questions already answered in a prior prep pass — this is what
    makes "click a link, it's already filled" fast (seconds, not the ~30s+ a
    fresh LLM-drafted pass takes) instead of redoing the same work.

    Every fill uses a [data-field-path="..."]-scoped selector, never a bare
    id — a real field (the Location combobox) has no id attribute at all, so
    id-based selectors silently skipped it entirely on a real run. data-field-path
    is present on every field's container regardless of the input inside it."""
    fields = page.evaluate(
        """() => Array.from(document.querySelectorAll('.ashby-application-form-field-entry')).map(entry => {
            const label = entry.querySelector('label');
            const desc = entry.querySelector('p');
            const yesnoButtons = Array.from(entry.querySelectorAll('button')).filter(
                b => ['Yes', 'No'].includes(b.textContent.trim())
            );
            const fileInput = entry.querySelector('input[type=file]');
            const selectEl = entry.querySelector('select');
            const comboEl = entry.querySelector('input[role="combobox"]');
            const input = entry.querySelector('input:not([type=checkbox]):not([type=file]):not([role=combobox]), textarea');
            return {
                question: label ? label.textContent.trim() : null,
                description: desc ? desc.textContent.trim() : null,
                fieldPath: entry.dataset.fieldPath,
                isYesNo: yesnoButtons.length === 2,
                isFile: !!fileInput,
                isSelect: !!selectEl,
                isCombobox: !!comboEl,
                hasTextInput: !!input,
            };
        })"""
    )

    answers_log = {}
    for field in fields:
        question = field["question"] or ""
        scoped = page.locator(f'[data-field-path="{field["fieldPath"]}"]')

        if field["isFile"] and "resume" in question.lower():
            pretty_name = f"{_profile_value(session, 'contact', 'full_name').replace(' ', '_')}_Resume.pdf"
            scoped.locator("input[type=file]").set_input_files(
                {"name": pretty_name, "mimeType": "application/pdf", "buffer": Path(job.resume_file_path).read_bytes()}
            )
            # A real run submitted with the resume widget silently empty — Ashby
            # processes the upload asynchronously (it re-parses the file for its
            # own autofill feature) and doesn't register as attached instantly.
            # Wait for the filename to actually render before treating this as done.
            try:
                scoped.get_by_text(pretty_name).wait_for(timeout=8000)
                answers_log[question] = f"[uploaded file as: {pretty_name}, confirmed attached]"
            except Exception:
                answers_log[question] = "NEEDS_HUMAN — resume upload did not visibly confirm attaching in time"
            continue

        if field["isYesNo"]:
            answer = _match_yesno_field(question, session, stored_answers)
            scoped.locator("button", has_text=answer).click()
            answers_log[question] = answer
            continue

        if field["isFile"]:
            continue  # an unhandled file field (not resume) needs a human, nothing to fill

        if "cover letter" in question.lower():
            value = job.cover_letter or ""
        elif stored_answers and question in stored_answers and not stored_answers[question].startswith("NEEDS_HUMAN"):
            value = stored_answers[question]
        else:
            value = _match_known_field(question, session)
            if value is None:
                # Every field gets a real, grounded answer — this is the whole
                # point of having a Profile Brain + real resume on file. Text
                # fields (short or long) go through the LLM grounded in both;
                # nothing is left blank by default just because it wasn't a
                # textarea.
                value = ask_premium(
                    ANSWER_PROMPT.format(
                        question=question,
                        description=field["description"] or "",
                        profile_summary=_profile_summary(session),
                        resume_text=(job.resume_text or "")[:3000],
                    )
                ).strip()

        if field["isSelect"] or field["isCombobox"]:
            if value:
                found, actual = _select_dropdown_option(page, scoped, value)
                answers_log[question] = actual if found else "NEEDS_HUMAN — no matching dropdown option found"
            else:
                answers_log[question] = value
            continue

        if not field["hasTextInput"]:
            answers_log[question] = "NEEDS_HUMAN — unrecognized field type, left unanswered"
            continue

        if value:
            scoped.locator("input, textarea").first.fill(value)
        answers_log[question] = value

    return answers_log


def _fill_greenhouse_form(page, job: Job, session, stored_answers: dict | None = None) -> dict:
    """Greenhouse's own hosted template (job-boards.greenhouse.io), verified
    by hand against a real live Airtable posting on 2026-07-27 — not guessed.
    Structurally different from Ashby: fields split across `.field-wrapper`
    (name/email/resume/custom questions) and `.eeoc__question__wrapper`
    (voluntary EEO self-ID), every field has a real, unique `id` (no id-less
    fields like Ashby's Location combobox), but MANY fields that render as
    plain dropdowns (Country, custom yes/no-style questions, all 4 EEO
    fields) are react-select comboboxes under the hood, not native <select>
    — confirmed by checking `select` vs `input[role=combobox]` directly
    rather than assuming from appearance. Also embeds an invisible reCAPTCHA
    Enterprise widget, so the same rule applies: never click Submit here."""
    fields = page.evaluate(
        """() => {
            const wrappers = Array.from(document.querySelectorAll(
                '.field-wrapper, .eeoc__question__wrapper, fieldset.phone-input'
            ));
            return wrappers.map(w => {
                const label = w.querySelector('label');
                const fileInput = w.querySelector('input[type=file]');
                const textarea = w.querySelector('textarea');
                const combo = w.querySelector('input[role=combobox]');
                const plainText = w.querySelector('input[type=text]:not([role=combobox])');
                let id = null, kind = null;
                if (fileInput) { id = fileInput.id; kind = 'file'; }
                else if (combo) { id = combo.id; kind = 'combobox'; }
                else if (textarea) { id = textarea.id; kind = 'textarea'; }
                else if (plainText) { id = plainText.id; kind = 'text'; }
                return {
                    question: label ? label.textContent.replace(/\\*$/, '').trim() : null,
                    id, kind,
                };
            }).filter(f => f.id);
        }"""
    )

    answers_log = {}
    for field in fields:
        question = field["question"] or ""
        scoped = page.locator(f'[id="{field["id"]}"]')

        if field["kind"] == "file":
            if field["id"] not in ("resume", "cover_letter"):
                continue  # optional extras (e.g. "upload an AI example") — nothing to attach, leave for a human
            content = job.resume_file_path if field["id"] == "resume" else None
            if field["id"] == "cover_letter":
                # Greenhouse accepts cover letter as a file OR handles it via
                # a text field elsewhere on some postings — this posting only
                # offers file upload, so skip; the cover_letter TEXT is only
                # used when a real text field/textarea asks for it below.
                continue
            pretty_name = f"{_profile_value(session, 'contact', 'full_name').replace(' ', '_')}_Resume.pdf"
            scoped.set_input_files({"name": pretty_name, "mimeType": "application/pdf", "buffer": Path(content).read_bytes()})
            page.wait_for_timeout(1500)  # Greenhouse doesn't show an inline filename confirmation like Ashby does
            answers_log[question] = f"[uploaded file as: {pretty_name}]"
            continue

        if "cover letter" in question.lower():
            value = job.cover_letter or ""
        elif stored_answers and question in stored_answers and not stored_answers[question].startswith("NEEDS_HUMAN"):
            value = stored_answers[question]
        elif "country" in question.lower():
            value = "United States"
        else:
            value = _match_known_field(question, session)
            if value is None and field["kind"] == "combobox" and question.lower().startswith(
                ("do you", "are you", "have you", "can you", "will you", "did you", "is this", "does this", "would you")
            ):
                # A real run fed a full drafted paragraph into these — dropdown
                # options here are just "Yes"/"No", and a paragraph doesn't
                # substring-match either one. Use the same short-answer path
                # Ashby's Yes/No buttons use instead of the long-form prompt.
                value = _match_yesno_field(question, session, stored_answers)
            elif value is None:
                value = ask_premium(
                    ANSWER_PROMPT.format(
                        question=question, description="", profile_summary=_profile_summary(session),
                        resume_text=(job.resume_text or "")[:3000],
                    )
                ).strip()

        if field["kind"] == "combobox":
            if value:
                found, actual = _select_dropdown_option(page, scoped, value)  # scoped IS the combobox input — Greenhouse ids every field
                answers_log[question] = actual if found else "NEEDS_HUMAN — no matching dropdown option found"
            else:
                answers_log[question] = value
            continue

        if value:
            scoped.fill(value)
        answers_log[question] = value

    return answers_log


def _goto_ashby_application(page, job_url: str) -> None:
    url = job_url if job_url.rstrip("/").endswith("/application") else job_url.rstrip("/") + "/application"
    page.goto(url)
    page.wait_for_timeout(1500)


def _goto_greenhouse_application(page, job_url: str) -> None:
    # Greenhouse's form lives on the SAME page as the posting, revealed by
    # an "Apply" button — no separate URL like Ashby's "/application" suffix.
    page.goto(job_url)
    page.wait_for_timeout(1500)
    apply_button = page.locator("button:has-text('Apply')").first
    if apply_button.count() > 0:
        apply_button.click()
        page.wait_for_timeout(1000)


ATS_HANDLERS = {
    "ashby": _fill_ashby_form,
    "greenhouse": _fill_greenhouse_form,
}

ATS_NAVIGATORS = {
    "ashby": _goto_ashby_application,
    "greenhouse": _goto_greenhouse_application,
}


def prepare_application(job_id: str) -> dict:
    """The "prep" pass — always headless, no visible window. Drafts every
    answer via the LLM (grounded in the Profile Brain + real resume) and
    stores the finished Application row. This is meant to run in bulk, in
    the background, for a whole batch of approved jobs at once, with nobody
    watching — see `reopen_application` for the fast, on-demand, VISIBLE
    step that reuses this pass's stored answers instead of redoing them.
    """
    session = get_session()
    job = session.get(Job, job_id)
    if not job:
        session.close()
        raise ValueError(f"job {job_id} not found")
    if not job.resume_file_path or not job.cover_letter:
        session.close()
        raise ValueError("job has no resume/cover letter yet — run Resume Selector + Cover Letter first")

    handler = ATS_HANDLERS.get(job.source)
    navigate = ATS_NAVIGATORS.get(job.source)
    if not handler or not navigate:
        session.close()
        raise ValueError(f"no Applier handler for source '{job.source}' yet (only {', '.join(ATS_HANDLERS)} are built)")

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = str((SCREENSHOT_DIR / f"{job.id}_{uuid.uuid4().hex[:8]}.png").resolve())

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    navigate(page, job.url)

    answers_log = handler(page, job, session)
    page.wait_for_timeout(300)
    page.screenshot(path=screenshot_path, full_page=True)
    browser.close()
    playwright.stop()

    needs_human = {q: a for q, a in answers_log.items() if isinstance(a, str) and a.startswith("NEEDS_HUMAN")}

    application = Application(
        job_id=job.id,
        resume_variant=job.resume_track or "",
        cover_letter=job.cover_letter or "",
        mode="semi_auto",
        submitted_via=job.source,
        status="needs_human_input" if needs_human else "ready_for_human_submit",
        approved_by_human=job.status == "approved",
        submitted_at=None,  # this code never marks anything submitted — only a human clicking Submit makes that true
        screenshot_path=screenshot_path,
        screening_answers=answers_log,
    )
    session.add(application)
    session.commit()
    application_id = str(application.id)
    session.close()

    return {
        "application_id": application_id,
        "status": application.status,
        "screenshot_path": screenshot_path,
        "answers": answers_log,
    }


def reopen_application(application_id: str, keep_open_seconds: int = 1800) -> dict:
    """The "click the link" step — opens a REAL VISIBLE Chromium window,
    right now, and re-fills the form using the answers already drafted and
    stored by `prepare_application` (no LLM calls for anything already
    answered, so this takes seconds, not the ~30s+ a fresh draft pass does).
    Leaves the window open for `keep_open_seconds` so there's no rush, but
    since the human just clicked to open this, it doesn't need the very long
    multi-hour window `prepare_application`'s batch use case would."""
    session = get_session()
    application = session.get(Application, application_id)
    if not application:
        session.close()
        raise ValueError(f"application {application_id} not found")
    job = session.get(Job, application.job_id)
    if not job:
        session.close()
        raise ValueError(f"job for application {application_id} not found")

    handler = ATS_HANDLERS.get(job.source)
    navigate = ATS_NAVIGATORS.get(job.source)
    if not handler or not navigate:
        session.close()
        raise ValueError(f"no Applier handler for source '{job.source}' yet (only {', '.join(ATS_HANDLERS)} are built)")

    screenshot_path = str((SCREENSHOT_DIR / f"{job.id}_{uuid.uuid4().hex[:8]}.png").resolve())

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    navigate(page, job.url)

    answers_log = handler(page, job, session, stored_answers=application.screening_answers)
    page.wait_for_timeout(300)
    page.screenshot(path=screenshot_path, full_page=True)

    needs_human = {q: a for q, a in answers_log.items() if isinstance(a, str) and a.startswith("NEEDS_HUMAN")}
    application.screenshot_path = screenshot_path
    application.screening_answers = answers_log
    application.status = "needs_human_input" if needs_human else "ready_for_human_submit"
    session.commit()
    session.close()

    if needs_human:
        print(f"[applier] Filled everything EXCEPT {len(needs_human)} question(s): {list(needs_human.keys())}. Fill those in yourself, then review and click Submit. Staying open for {keep_open_seconds}s.")
    else:
        print(f"[applier] Form re-filled and ready. Review it, then click Submit yourself. Staying open for {keep_open_seconds}s.")
    try:
        page.wait_for_timeout(keep_open_seconds * 1000)
    except Exception:
        pass  # the human closed the browser themselves (e.g. after submitting) — expected, not an error

    try:
        browser.close()
    except Exception:
        pass
    playwright.stop()

    return {"status": "reopened", "screenshot_path": screenshot_path, "answers": answers_log}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m jarvis.agents.applier prepare <job_id>\n       python -m jarvis.agents.applier reopen <application_id>")
        sys.exit(1)
    if sys.argv[1] == "reopen":
        result = reopen_application(sys.argv[2])
    else:
        result = prepare_application(sys.argv[1] if sys.argv[1] != "prepare" else sys.argv[2])
    print(json.dumps(result, indent=2))
