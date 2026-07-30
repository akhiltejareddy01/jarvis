// Frontend-only persistence until the FastAPI backend exists (per the build
// order: frontend first, backend next). Swap these for real fetch() calls to
// the API layer later — callers already treat this as async so that swap
// doesn't ripple through components.

import { DailyIntake, Profile } from "./types";

const PROFILE_KEY = "sara_job_profile";
const INTAKE_PREFIX = "sara_job_intake_";

export async function loadProfile(): Promise<Profile | null> {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(PROFILE_KEY);
  return raw ? (JSON.parse(raw) as Profile) : null;
}

export async function saveProfile(profile: Profile): Promise<void> {
  window.localStorage.setItem(
    PROFILE_KEY,
    JSON.stringify({ ...profile, updatedAt: new Date().toISOString() })
  );
}

export async function loadIntake(runDate: string): Promise<DailyIntake | null> {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(INTAKE_PREFIX + runDate);
  return raw ? (JSON.parse(raw) as DailyIntake) : null;
}

export async function saveIntake(intake: DailyIntake): Promise<void> {
  window.localStorage.setItem(INTAKE_PREFIX + intake.runDate, JSON.stringify(intake));
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

// new Date("YYYY-MM-DD") parses as UTC midnight, which renders as the wrong
// calendar day in timezones behind UTC. Parse as local instead.
export function parseLocalDate(isoDate: string): Date {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d);
}
