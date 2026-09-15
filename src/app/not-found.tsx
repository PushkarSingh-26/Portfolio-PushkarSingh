import Link from "next/link";
import { DocumentTitle } from "./DocumentTitle";

export default function NotFound() {
  return (
    <div className="wrap py-24 md:py-40">
      <DocumentTitle title="Page not found — Pushkar Singh" />
      <p className="mono text-ink-2">404</p>
      <h1 className="h-section mt-4 max-w-[16ch]">There’s nothing at this address.</h1>
      <p className="lead measure mt-6">The link may be old, or mistyped. Everything on the site is reachable from the overview.</p>
      <div className="mt-10 flex flex-wrap gap-3">
        <Link className="btn btn-primary" href="/">
          Go to the overview
        </Link>
        <Link className="btn btn-secondary" href="/resume">
          Read the résumé
        </Link>
      </div>
    </div>
  );
}
