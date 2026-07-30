import { SampleDataBanner } from "@/components/SampleDataBanner";
import { MOCK_REPORTS } from "@/lib/mockData";
import { parseLocalDate } from "@/lib/storage";

export default function ReportsPage() {
  return (
    <main className="max-w-3xl mx-auto px-6 py-10 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Daily Reports</h1>
        <p className="text-sm text-neutral-500 mt-1">
          Nightly reflection: real statistics first (reply rates per track/company
          type/resume variant), then a human-readable journal entry — numbers lead, language
          follows.
        </p>
      </div>

      <SampleDataBanner agent="Reflection (nightly)" />

      {MOCK_REPORTS.map((r) => (
        <div key={r.date} className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-6 flex flex-col gap-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              {parseLocalDate(r.date).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}
            </h2>
          </div>

          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3">
              <div className="text-xl font-bold">{r.applied}</div>
              <div className="text-xs text-neutral-500">Applied</div>
            </div>
            <div className="rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3">
              <div className="text-xl font-bold">{r.skipped}</div>
              <div className="text-xs text-neutral-500">Skipped</div>
            </div>
            <div className="rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3">
              <div className="text-xl font-bold">{r.drafted}</div>
              <div className="text-xs text-neutral-500">Drafted</div>
            </div>
            <div className="rounded-lg bg-neutral-50 dark:bg-neutral-900 p-3">
              <div className="text-xl font-bold">{r.followUpsDue}</div>
              <div className="text-xs text-neutral-500">Follow-ups due</div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-neutral-500 mb-2">Reply rates by track</h3>
            <div className="flex flex-col gap-2">
              {r.statsByTrack.map((s) => (
                <div key={s.label} className="flex items-center gap-3 text-sm">
                  <span className="w-40 shrink-0">{s.label}</span>
                  <div className="flex-1 h-2 rounded-full bg-neutral-100 dark:bg-neutral-900 overflow-hidden">
                    <div className="h-full bg-indigo-500" style={{ width: `${s.replyRate * 100}%` }} />
                  </div>
                  <span className="text-neutral-500 w-24 text-right">{s.replies}/{s.applied} replies</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-neutral-500 mb-2">Journal entry</h3>
            <p className="text-sm text-neutral-700 dark:text-neutral-300 rounded-lg bg-neutral-50 dark:bg-neutral-900 p-4">
              {r.journalEntry}
            </p>
          </div>
        </div>
      ))}
    </main>
  );
}
