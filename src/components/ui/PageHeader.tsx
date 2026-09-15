import Link from "next/link";
import type { ReactNode } from "react";

/**
 * Header for case-study and research pages. `facts` render as a definition list —
 * real label/value pairs, not decorative eyebrows.
 */
export function PageHeader({
  title,
  lead,
  facts = [],
  actions,
  back = { href: "/", label: "Back to the overview" },
}: {
  title: string;
  lead?: ReactNode;
  facts?: { label: string; value: ReactNode }[];
  actions?: ReactNode;
  back?: { href: string; label: string };
}) {
  return (
    <header className="wrap pt-10 pb-12 md:pt-16 md:pb-20">
      <Link href={back.href} className="link small inline-block mb-10 md:mb-14">
        {back.label}
      </Link>
      <h1 className="h-section max-w-[18ch]">{title}</h1>
      {lead && <div className="lead measure mt-6">{lead}</div>}
      {facts.length > 0 && (
        <dl className="mt-10 grid grid-cols-1 gap-x-10 gap-y-4 sm:grid-cols-2 lg:grid-cols-4 max-w-5xl">
          {facts.map((f) => (
            <div key={f.label} className="border-t border-rule pt-3">
              <dt className="small text-ink-2">{f.label}</dt>
              <dd className="mt-1 font-semibold">{f.value}</dd>
            </div>
          ))}
        </dl>
      )}
      {actions && <div className="mt-10 flex flex-wrap gap-3">{actions}</div>}
    </header>
  );
}
