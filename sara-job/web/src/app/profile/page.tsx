"use client";

import { useEffect, useState } from "react";
import { Field, Section, inputClass } from "@/components/Field";
import { TagInput } from "@/components/TagInput";
import { loadProfile, saveProfile } from "@/lib/storage";
import { SEED_PROFILE } from "@/lib/seedProfile";
import { Profile, ResumeVariant, ScreeningAnswer } from "@/lib/types";

const WORK_AUTH_OPTIONS = [
  "US Citizen",
  "Green Card / Permanent Resident",
  "H1B",
  "OPT/CPT",
  "Need Sponsorship",
  "Other",
];

const NOTICE_OPTIONS = ["Immediate", "2 weeks", "1 month", "2 months", "Other"];

const EEO_OPTIONS_GENDER = ["Decline to answer", "Male", "Female", "Non-binary", "Other"];
const EEO_OPTIONS_RACE = [
  "Decline to answer",
  "American Indian or Alaska Native",
  "Asian",
  "Black or African American",
  "Hispanic or Latino",
  "Native Hawaiian or Other Pacific Islander",
  "White",
  "Two or more races",
];
const EEO_OPTIONS_VETERAN = ["Decline to answer", "I am a veteran", "I am not a veteran"];
const EEO_OPTIONS_DISABILITY = [
  "Decline to answer",
  "Yes, I have a disability",
  "No, I do not have a disability",
];

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>(SEED_PROFILE);
  const [loaded, setLoaded] = useState(false);
  const [usingSeed, setUsingSeed] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    loadProfile().then((p) => {
      if (p) {
        setProfile(p);
      } else {
        setProfile(SEED_PROFILE);
        setUsingSeed(true);
      }
      setLoaded(true);
    });
  }, []);

  function resetToSeed() {
    setProfile(SEED_PROFILE);
    setUsingSeed(true);
  }

  function update<K extends keyof Profile>(key: K, value: Profile[K]) {
    setProfile((p) => ({ ...p, [key]: value }));
  }

  function updateResume(index: number, patch: Partial<ResumeVariant>) {
    setProfile((p) => ({
      ...p,
      resumes: p.resumes.map((r, i) => (i === index ? { ...r, ...patch } : r)),
    }));
  }

  function addResume() {
    setProfile((p) => ({
      ...p,
      resumes: [...p.resumes, { track: "", fileName: "", notes: "" }],
    }));
  }

  function removeResume(index: number) {
    setProfile((p) => ({ ...p, resumes: p.resumes.filter((_, i) => i !== index) }));
  }

  function updateAnswer(index: number, patch: Partial<ScreeningAnswer>) {
    setProfile((p) => ({
      ...p,
      screeningAnswers: p.screeningAnswers.map((a, i) => (i === index ? { ...a, ...patch } : a)),
    }));
  }

  function addAnswer() {
    setProfile((p) => ({
      ...p,
      screeningAnswers: [...p.screeningAnswers, { question: "", answer: "" }],
    }));
  }

  function removeAnswer(index: number) {
    setProfile((p) => ({
      ...p,
      screeningAnswers: p.screeningAnswers.filter((_, i) => i !== index),
    }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    await saveProfile(profile);
    setSavedAt(new Date().toLocaleTimeString());
  }

  if (!loaded) return null;

  return (
    <main className="max-w-3xl mx-auto px-6 py-10 flex flex-col gap-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Your Profile</h1>
          <p className="text-sm text-neutral-500 mt-1">
            Fill this in once — this is what Sara pulls from to score jobs, tailor resumes, and
            answer screening questions. Come back and edit only when something actually changes.
          </p>
        </div>
        <button
          type="button"
          onClick={resetToSeed}
          className="shrink-0 text-sm font-medium text-indigo-600 hover:text-indigo-800"
        >
          Reload from resumes
        </button>
      </div>

      {usingSeed && (
        <div className="rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-200 text-sm px-4 py-2.5">
          Pre-filled from your 11 resumes in <code>E:\AKHIL\Resumes</code>. <strong>Double-check
          work authorization and the screening answers below</strong> — those were guessed or
          left as placeholders and haven&apos;t been confirmed by you yet.
        </div>
      )}

      <form onSubmit={handleSave} className="flex flex-col gap-6">
        <Section title="Basics">
          <Field label="Full name">
            <input className={inputClass} value={profile.fullName} onChange={(e) => update("fullName", e.target.value)} />
          </Field>
          <Field label="Email">
            <input className={inputClass} type="email" value={profile.email} onChange={(e) => update("email", e.target.value)} />
          </Field>
          <Field label="Phone">
            <input className={inputClass} value={profile.phone} onChange={(e) => update("phone", e.target.value)} />
          </Field>
          <Field label="LinkedIn URL">
            <input className={inputClass} value={profile.linkedinUrl} onChange={(e) => update("linkedinUrl", e.target.value)} />
          </Field>
          <Field label="GitHub URL">
            <input className={inputClass} value={profile.githubUrl} onChange={(e) => update("githubUrl", e.target.value)} />
          </Field>
          <Field label="Portfolio URL">
            <input className={inputClass} value={profile.portfolioUrl} onChange={(e) => update("portfolioUrl", e.target.value)} />
          </Field>
        </Section>

        <Section title="Job preferences" description="Drives the daily job scout and fit scoring.">
          <Field label="Target roles" hint="Press Enter to add each one">
            <TagInput values={profile.targetRoles} onChange={(v) => update("targetRoles", v)} placeholder="Backend Engineer, Data Engineer..." />
          </Field>
          <Field label="Years of experience">
            <input
              className={inputClass}
              type="number"
              min={0}
              value={profile.experienceYears}
              onChange={(e) => update("experienceYears", Number(e.target.value))}
            />
          </Field>
          <Field label="Locations" hint="Press Enter to add each one">
            <TagInput values={profile.locations} onChange={(v) => update("locations", v)} placeholder="Austin TX, Remote..." />
          </Field>
          <Field label="Open to remote?">
            <select
              className={inputClass}
              value={profile.remoteOk ? "yes" : "no"}
              onChange={(e) => update("remoteOk", e.target.value === "yes")}
            >
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </Field>
          <Field label="Salary floor (min, USD)">
            <input
              className={inputClass}
              type="number"
              min={0}
              value={profile.salaryMin}
              onChange={(e) => update("salaryMin", Number(e.target.value))}
            />
          </Field>
          <Field label="Salary target (max, USD)">
            <input
              className={inputClass}
              type="number"
              min={0}
              value={profile.salaryMax}
              onChange={(e) => update("salaryMax", Number(e.target.value))}
            />
          </Field>
        </Section>

        <Section title="Work authorization" description="Used to auto-answer standard screening questions.">
          <Field label="Work authorization status">
            <select className={inputClass} value={profile.workAuthorization} onChange={(e) => update("workAuthorization", e.target.value)}>
              {WORK_AUTH_OPTIONS.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </Field>
          <Field label="Notice period">
            <select className={inputClass} value={profile.noticePeriod} onChange={(e) => update("noticePeriod", e.target.value)}>
              {NOTICE_OPTIONS.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </Field>
        </Section>

        <section className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Resume variants</h2>
              <p className="text-sm text-neutral-500 mt-0.5">
                Your different resume versions by track. Actual file upload connects once the
                backend is wired — for now just name the file and track.
              </p>
            </div>
            <button type="button" onClick={addResume} className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
              + Add resume
            </button>
          </div>
          {profile.resumes.length === 0 && (
            <p className="text-sm text-neutral-500">No resume variants added yet.</p>
          )}
          {profile.resumes.map((r, i) => (
            <div key={i} className="grid grid-cols-1 sm:grid-cols-[1fr_1fr_2fr_auto] gap-3 items-start">
              <input className={inputClass} placeholder="Track (e.g. Backend)" value={r.track} onChange={(e) => updateResume(i, { track: e.target.value })} />
              <input className={inputClass} placeholder="File name" value={r.fileName} onChange={(e) => updateResume(i, { fileName: e.target.value })} />
              <input className={inputClass} placeholder="Notes" value={r.notes} onChange={(e) => updateResume(i, { notes: e.target.value })} />
              <button type="button" onClick={() => removeResume(i)} className="text-sm text-red-600 hover:text-red-800 px-2 py-2">
                Remove
              </button>
            </div>
          ))}
        </section>

        <section className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">Standard screening answers</h2>
              <p className="text-sm text-neutral-500 mt-0.5">
                Common application questions and your canned answers (e.g. &quot;Why this
                company?&quot;, &quot;Notice period?&quot;).
              </p>
            </div>
            <button type="button" onClick={addAnswer} className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
              + Add answer
            </button>
          </div>
          {profile.screeningAnswers.length === 0 && (
            <p className="text-sm text-neutral-500">No standard answers added yet.</p>
          )}
          {profile.screeningAnswers.map((a, i) => (
            <div key={i} className="grid grid-cols-1 sm:grid-cols-[1fr_2fr_auto] gap-3 items-start">
              <input className={inputClass} placeholder="Question" value={a.question} onChange={(e) => updateAnswer(i, { question: e.target.value })} />
              <textarea className={inputClass} placeholder="Answer" value={a.answer} onChange={(e) => updateAnswer(i, { answer: e.target.value })} rows={2} />
              <button type="button" onClick={() => removeAnswer(i)} className="text-sm text-red-600 hover:text-red-800 px-2 py-2">
                Remove
              </button>
            </div>
          ))}
        </section>

        <details className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
          <summary className="cursor-pointer text-lg font-semibold">
            EEO self-identification <span className="text-sm font-normal text-neutral-500">(optional, defaults to decline)</span>
          </summary>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mt-5">
            <Field label="Gender">
              <select className={inputClass} value={profile.eeoGender} onChange={(e) => update("eeoGender", e.target.value)}>
                {EEO_OPTIONS_GENDER.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Race / ethnicity">
              <select className={inputClass} value={profile.eeoRace} onChange={(e) => update("eeoRace", e.target.value)}>
                {EEO_OPTIONS_RACE.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Veteran status">
              <select className={inputClass} value={profile.eeoVeteranStatus} onChange={(e) => update("eeoVeteranStatus", e.target.value)}>
                {EEO_OPTIONS_VETERAN.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Disability status">
              <select className={inputClass} value={profile.eeoDisabilityStatus} onChange={(e) => update("eeoDisabilityStatus", e.target.value)}>
                {EEO_OPTIONS_DISABILITY.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
          </div>
        </details>

        <div className="flex items-center gap-4">
          <button type="submit" className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-5 py-2.5 text-sm">
            Save profile
          </button>
          {savedAt && <span className="text-sm text-neutral-500">Saved at {savedAt}</span>}
        </div>
      </form>
    </main>
  );
}
