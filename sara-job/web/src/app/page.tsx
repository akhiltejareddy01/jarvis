"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Field, inputClass } from "@/components/Field";
import { TagInput } from "@/components/TagInput";
import { loadIntake, loadProfile, saveIntake, todayIso } from "@/lib/storage";
import { DailyIntake, Profile, dailyIntakeFromProfile } from "@/lib/types";

export default function TodayPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [intake, setIntake] = useState<DailyIntake | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      const p = await loadProfile();
      setProfile(p);
      if (p) {
        const existing = await loadIntake(todayIso());
        setIntake(existing ?? dailyIntakeFromProfile(p, todayIso()));
      }
      setLoaded(true);
    })();
  }, []);

  function update<K extends keyof DailyIntake>(key: K, value: DailyIntake[K]) {
    setIntake((i) => (i ? { ...i, [key]: value } : i));
  }

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    if (!intake) return;
    setSaving(true);
    try {
      const started: DailyIntake = { ...intake, status: "started" };
      await saveIntake(started);
      setIntake(started);
    } finally {
      setSaving(false);
    }
  }

  async function handleEdit() {
    if (!intake) return;
    await saveIntake({ ...intake, status: "pending" });
    setIntake({ ...intake, status: "pending" });
  }

  if (!loaded) return null;

  if (!profile) {
    return (
      <main className="max-w-xl mx-auto px-6 py-20 text-center flex flex-col items-center gap-4">
        <h1 className="text-2xl font-bold">Set up your profile first</h1>
        <p className="text-sm text-neutral-500">
          Sara needs your roles, locations, salary range, and resumes before she can plan a
          daily run.
        </p>
        <Link href="/profile" className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-5 py-2.5 text-sm">
          Go to Profile
        </Link>
      </main>
    );
  }

  if (!intake) return null;

  const started = intake.status !== "pending";

  return (
    <main className="max-w-2xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Today&apos;s plan</h1>
        <p className="text-sm text-neutral-500 mt-1">
          {new Date().toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          {" — "}pre-filled from your profile, edit anything that&apos;s different today.
        </p>
      </div>

      {started ? (
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-6 flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-sm font-medium">Run started — status: {intake.status}</span>
          </div>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <dt className="text-neutral-500">Track</dt><dd>{intake.track || "—"}</dd>
            <dt className="text-neutral-500">Locations</dt><dd>{intake.locations.join(", ") || "—"}</dd>
            <dt className="text-neutral-500">Salary floor</dt><dd>${intake.salaryFloor.toLocaleString()}</dd>
            <dt className="text-neutral-500">Target count</dt><dd>{intake.targetCount}</dd>
            <dt className="text-neutral-500">Mode</dt><dd>{intake.mode === "semi_auto" ? "Semi-auto (approve each)" : "Mostly-auto"}</dd>
            <dt className="text-neutral-500">Focus companies</dt><dd>{intake.focusCompanies.join(", ") || "None"}</dd>
            <dt className="text-neutral-500">Avoid companies</dt><dd>{intake.avoidCompanies.join(", ") || "None"}</dd>
          </dl>
          <p className="text-sm text-neutral-500">
            The job queue below will populate once the Scout agent is built (next phase).
          </p>
          <button onClick={handleEdit} className="self-start text-sm font-medium text-indigo-600 hover:text-indigo-800">
            Edit today&apos;s plan
          </button>
        </div>
      ) : (
        <form onSubmit={handleStart} className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-6 flex flex-col gap-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <Field label="Track / role focus for today">
              <input className={inputClass} value={intake.track} onChange={(e) => update("track", e.target.value)} />
            </Field>
            <Field label="Salary floor (USD)">
              <input className={inputClass} type="number" value={intake.salaryFloor} onChange={(e) => update("salaryFloor", Number(e.target.value))} />
            </Field>
            <Field label="Locations">
              <TagInput values={intake.locations} onChange={(v) => update("locations", v)} placeholder="Add a location..." />
            </Field>
            <Field label="Target count">
              <input className={inputClass} type="number" value={intake.targetCount} onChange={(e) => update("targetCount", Number(e.target.value))} />
            </Field>
            <Field label="Mode">
              <select className={inputClass} value={intake.mode} onChange={(e) => update("mode", e.target.value as DailyIntake["mode"])}>
                <option value="semi_auto">Semi-auto (approve each)</option>
                <option value="auto">Mostly-auto</option>
              </select>
            </Field>
            <Field label="Focus companies today" hint="optional">
              <TagInput values={intake.focusCompanies} onChange={(v) => update("focusCompanies", v)} placeholder="Add a company..." />
            </Field>
            <Field label="Avoid companies today" hint="optional">
              <TagInput values={intake.avoidCompanies} onChange={(v) => update("avoidCompanies", v)} placeholder="Add a company..." />
            </Field>
          </div>
          <button type="submit" disabled={saving} className="self-start rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-5 py-2.5 text-sm">
            {saving ? "Starting..." : "Start today's run"}
          </button>
        </form>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-2">Jobs queue</h2>
        <p className="text-sm text-neutral-500">
          Empty — the Job Scout (next build phase) hasn&apos;t populated this yet.
        </p>
      </section>
    </main>
  );
}
