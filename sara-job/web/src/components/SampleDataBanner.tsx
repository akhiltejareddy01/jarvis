export function SampleDataBanner({ agent }: { agent: string }) {
  return (
    <div className="rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-800 dark:text-amber-200 text-sm px-4 py-2.5">
      Sample data — this page previews the real layout. It goes live once the{" "}
      <strong>{agent}</strong> agent and backend are built.
    </div>
  );
}
