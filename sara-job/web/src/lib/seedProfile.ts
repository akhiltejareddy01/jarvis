// Real profile data extracted from Akhil's actual resumes (E:\AKHIL\Resumes) —
// used as a one-click seed on the Profile page instead of retyping everything.
// Resume PDFs themselves live in D:\JARVIS\sara-job\resumes (gitignored); actual
// upload/storage wiring comes with the backend, this just records filenames + tracks.

import { Profile } from "./types";

export const SEED_PROFILE: Profile = {
  fullName: "Venkata Akhil Teja Reddy Yamasani",
  email: "yvakhilteja1104@gmail.com",
  phone: "+1 716 709 1439",
  linkedinUrl: "linkedin.com/in/venkata-akhil-teja-reddy",
  githubUrl: "",
  portfolioUrl: "",

  targetRoles: [
    "AI Engineer",
    "Software Engineer",
    "Data Engineer",
    "Machine Learning Engineer",
    "Data Scientist",
  ],
  experienceYears: 3,
  locations: ["New York, NY", "Remote"],
  remoteOk: true,
  salaryMin: 100000,
  salaryMax: 160000,

  // Confirmed directly by Akhil on 2026-07-27 (was previously an unconfirmed guess).
  // Must exactly match one of the <select> options in the Profile form below —
  // an unmatched string silently falls back to showing the first option ("US
  // Citizen") instead of erroring, which is a real trap (looked right, wasn't).
  workAuthorization: "OPT/CPT",
  noticePeriod: "Immediate",

  resumes: [
    { track: "AI Engineer", fileName: "Ai_Engineer_Venkata_Akhil_Teja_Reddy.pdf", notes: "GenAI, RAG & LLM Agents · Python, FastAPI, PostgreSQL" },
    { track: "Software Engineer", fileName: "Software_Engineer_Venkata_Akhil_Teja_Reddy.pdf", notes: "Python Microservices & REST APIs · FastAPI, PostgreSQL, CI/CD" },
    { track: "Data Engineer", fileName: "Data_Engineer_Venkata_Akhil_Teja_Reddy.pdf", notes: "ETL, SQL & Data Modeling · Python, PostgreSQL, AWS" },
    { track: "Machine Learning Engineer", fileName: "Machine_Learning_Venkata_Akhil_Teja_Reddy.pdf", notes: "NLP & Predictive Modeling · Python, MLOps, AWS" },
    { track: "Data Scientist", fileName: "Data_Scientist_Venkata_Akhil_Teja_Reddy.pdf", notes: "Machine Learning, NLP & Statistics · Python, SQL, AWS" },
    { track: "Data Analyst", fileName: "Data_Analyst_Venkata_Akhil_Teja_Reddy.pdf", notes: "SQL, Power BI & Tableau · Python, Dashboards & Insights" },
    { track: "Business Analyst", fileName: "Business_Analyst_Venkata_Akhil_Teja_Reddy.pdf", notes: "Requirements, Analytics & Reporting · SQL, Power BI, Tableau" },
    { track: "QA Analyst", fileName: "QA_Analyst_Venkata_Akhil_Teja_Reddy.pdf", notes: "Quality Assurance & Test Automation · Python, SQL, CI/CD" },
    { track: "Software Tester", fileName: "Software_Tester_Venkata_Akhil_Teja_Reddy.pdf", notes: "API & Data Validation Testing · Python, SQL, CI/CD" },
    { track: "GTM Engineer", fileName: "GTM_Venkata_Akhil_Teja_Reddy.pdf", notes: "AI-Driven Lead Generation & Growth Experiments · Python, Automation, Analytics" },
    { track: "PLM", fileName: "PLM_Venkata_Akhil_Teja_Reddy.pdf", notes: "Configuration Management & PLM · Change management, product data" },
  ],

  screeningAnswers: [
    { question: "Why this company?", answer: "Placeholder — write a real answer per company, or let Sara draft one from the JD once the backend is live." },
    { question: "What is your notice period?", answer: "Immediate." },
    { question: "Are you authorized to work in the US?", answer: "Yes, I am authorized to work in the US (F-1 OPT)." },
    { question: "Will you now or in the future require visa sponsorship?", answer: "No." },
    { question: "Desired salary?", answer: "$100,000–$160,000 depending on role and location." },
  ],

  eeoGender: "Decline to answer",
  eeoRace: "Decline to answer",
  eeoVeteranStatus: "Decline to answer",
  eeoDisabilityStatus: "Decline to answer",

  updatedAt: "",
};
