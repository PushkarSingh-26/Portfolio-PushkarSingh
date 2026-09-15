import Link from "next/link";
import { profile } from "@/content/profile";

export function SiteFooter() {
  return (
    <footer className="no-print border-t border-rule mt-8">
      <div className="wrap py-10 md:py-14 grid gap-8 md:grid-cols-12">
        <p className="small text-ink-2 md:col-span-6 measure">
          Illustrations and demo data are labelled where they appear.
        </p>
        <ul className="small md:col-span-6 flex flex-wrap gap-x-6 gap-y-2 md:justify-end">
          <li>
            <a className="link" href={`mailto:${profile.email}`}>
              Email
            </a>
          </li>
          <li>
            <a className="link" href={profile.links.linkedin} target="_blank" rel="noreferrer">
              LinkedIn
            </a>
          </li>
          <li>
            <a className="link" href={profile.links.github} target="_blank" rel="noreferrer">
              GitHub
            </a>
          </li>
          <li>
            <a className="link" href={profile.links.leetcode} target="_blank" rel="noreferrer">
              LeetCode
            </a>
          </li>
          <li>
            <a className="link" href={profile.links.tensortonic} target="_blank" rel="noreferrer">
              Tensortonic
            </a>
          </li>
          <li>
            <Link className="link" href="/resume">
              Résumé
            </Link>
          </li>
        </ul>
        <p className="small text-ink-2 md:col-span-12">© 2026 {profile.name}</p>
      </div>
    </footer>
  );
}
