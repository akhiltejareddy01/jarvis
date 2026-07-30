"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { section: "Daily", items: [{ href: "/", label: "Today" }] },
  {
    section: "Pipeline",
    items: [
      { href: "/jobs", label: "Jobs" },
      { href: "/applications", label: "Applications" },
      { href: "/contacts", label: "Contacts & Outreach" },
      { href: "/follow-ups", label: "Follow-ups" },
      { href: "/replies", label: "Email Replies" },
    ],
  },
  {
    section: "The brain",
    items: [
      { href: "/reports", label: "Daily Reports" },
      { href: "/strategy", label: "Strategy Profile" },
    ],
  },
  {
    section: "System",
    items: [
      { href: "/audit", label: "Audit & Guardrails" },
      { href: "/profile", label: "Profile" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 border-r border-neutral-200 dark:border-neutral-800 flex flex-col gap-6 px-4 py-6">
      <div className="px-2">
        <span className="font-bold text-lg">Sara Job</span>
      </div>
      <nav className="flex flex-col gap-5">
        {NAV.map((group) => (
          <div key={group.section} className="flex flex-col gap-1">
            <span className="px-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
              {group.section}
            </span>
            {group.items.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-md px-2 py-1.5 text-sm ${
                    active
                      ? "bg-indigo-600 text-white font-medium"
                      : "text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-900"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
    </aside>
  );
}
