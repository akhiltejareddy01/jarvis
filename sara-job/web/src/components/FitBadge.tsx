import { FitRating } from "@/lib/types";

const STYLES: Record<FitRating, string> = {
  strong: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  medium: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  weak: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
};

export function FitBadge({ rating }: { rating: FitRating | null }) {
  if (!rating) {
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-neutral-100 text-neutral-500 dark:bg-neutral-900 dark:text-neutral-400">
        unscored
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${STYLES[rating]}`}>
      {rating}
    </span>
  );
}

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-neutral-100 text-neutral-700 dark:bg-neutral-900 dark:text-neutral-300",
  approved: "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300",
  submitted: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  interview: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  rejected: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  pending: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  sent: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
  skipped: "bg-neutral-100 text-neutral-500 dark:bg-neutral-900 dark:text-neutral-400",
  new: "bg-neutral-100 text-neutral-700 dark:bg-neutral-900 dark:text-neutral-300",
  pending_review: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  ready_for_human_submit: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  not_submitted: "bg-neutral-100 text-neutral-500 dark:bg-neutral-900 dark:text-neutral-400",
  needs_human_input: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  unverified: "bg-neutral-100 text-neutral-500 dark:bg-neutral-900 dark:text-neutral-400",
  pending_review_strategy: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
};

export function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_STYLES[status] ?? STATUS_STYLES.draft;
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
