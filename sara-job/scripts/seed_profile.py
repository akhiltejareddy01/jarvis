"""Seed profile_facts / resume_variants / screening_answers from the real
resume data (same source as web/src/lib/seedProfile.ts) so Scout/Fit Scorer
have a real profile to work against before the frontend<->backend sync
(profile currently lives only in browser localStorage) is built.

Safe to re-run — upserts by unique key.

Usage:  python scripts/seed_profile.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects.postgresql import insert

from jarvis.db.models import ProfileFact, ResumeVariant, ScreeningAnswer
from jarvis.db.session import get_session

FACTS = {
    "contact": {
        "full_name": "Venkata Akhil Teja Reddy Yamasani",
        "email": "yvakhilteja1104@gmail.com",
        "phone": "+1 716 709 1439",
        "linkedin_url": "linkedin.com/in/venkata-akhil-teja-reddy",
    },
    "preferences": {
        "target_roles": "AI Engineer, Software Engineer, Data Engineer, Machine Learning Engineer, Data Scientist",
        "locations": "New York NY, Remote",
        "remote_ok": "true",
        "experience_years": "3",
    },
    "compensation": {
        "salary_min": "100000",
        "salary_max": "160000",
    },
    "work_auth": {
        # Guessed from resume timeline (MPS Aug'24-Dec'25, then employed Jan'26) — likely OPT.
        # UNCONFIRMED — do not rely on this for a real application without checking with Akhil.
        "status": "OPT/CPT (unconfirmed — verify before real use)",
        "notice_period": "Immediate",
    },
}

RESUMES = [
    ("AI Engineer", "Ai_Engineer_Venkata_Akhil_Teja_Reddy.pdf", "GenAI, RAG & LLM Agents · Python, FastAPI, PostgreSQL"),
    ("Software Engineer", "Software_Engineer_Venkata_Akhil_Teja_Reddy.pdf", "Python Microservices & REST APIs · FastAPI, PostgreSQL, CI/CD"),
    ("Data Engineer", "Data_Engineer_Venkata_Akhil_Teja_Reddy.pdf", "ETL, SQL & Data Modeling · Python, PostgreSQL, AWS"),
    ("Machine Learning Engineer", "Machine_Learning_Venkata_Akhil_Teja_Reddy.pdf", "NLP & Predictive Modeling · Python, MLOps, AWS"),
    ("Data Scientist", "Data_Scientist_Venkata_Akhil_Teja_Reddy.pdf", "Machine Learning, NLP & Statistics · Python, SQL, AWS"),
    ("Data Analyst", "Data_Analyst_Venkata_Akhil_Teja_Reddy.pdf", "SQL, Power BI & Tableau · Python, Dashboards & Insights"),
    ("Business Analyst", "Business_Analyst_Venkata_Akhil_Teja_Reddy.pdf", "Requirements, Analytics & Reporting · SQL, Power BI, Tableau"),
    ("QA Analyst", "QA_Analyst_Venkata_Akhil_Teja_Reddy.pdf", "Quality Assurance & Test Automation · Python, SQL, CI/CD"),
    ("Software Tester", "Software_Tester_Venkata_Akhil_Teja_Reddy.pdf", "API & Data Validation Testing · Python, SQL, CI/CD"),
    ("GTM Engineer", "GTM_Venkata_Akhil_Teja_Reddy.pdf", "AI-Driven Lead Generation & Growth Experiments · Python, Automation, Analytics"),
    ("PLM", "PLM_Venkata_Akhil_Teja_Reddy.pdf", "Configuration Management & PLM · Change management, product data"),
]

SCREENING_ANSWERS = [
    ("why_this_company", "Why this company?", "Placeholder — write a real answer per company, or let Sara draft one from the JD once that's built."),
    ("notice_period", "What is your notice period?", "Immediate."),
    ("work_authorization", "Are you authorized to work in the US?", "PLACEHOLDER — confirm exact current visa/work-authorization status before this is used on any real application."),
    ("desired_salary", "Desired salary?", "$100,000-$160,000 depending on role and location."),
]


def main() -> None:
    session = get_session()

    for category, kv in FACTS.items():
        for key, value in kv.items():
            stmt = insert(ProfileFact).values(category=category, key=key, value=value)
            stmt = stmt.on_conflict_do_update(
                index_elements=["category", "key"], set_={"value": value}
            )
            session.execute(stmt)

    for track, file_name, notes in RESUMES:
        stmt = insert(ResumeVariant).values(track=track, file_name=file_name, notes=notes)
        stmt = stmt.on_conflict_do_update(
            index_elements=["track"], set_={"file_name": file_name, "notes": notes}
        )
        session.execute(stmt)

    for question_key, question_text, answer in SCREENING_ANSWERS:
        stmt = insert(ScreeningAnswer).values(
            question_key=question_key, question_text=question_text, answer=answer
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["question_key"], set_={"answer": answer}
        )
        session.execute(stmt)

    session.commit()
    session.close()
    print(f"Seeded {sum(len(v) for v in FACTS.values())} facts, {len(RESUMES)} resume variants, {len(SCREENING_ANSWERS)} screening answers.")


if __name__ == "__main__":
    main()
