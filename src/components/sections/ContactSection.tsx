import Image from "next/image";
import tokens from "@/content/generated/tokens.json";
import { portraitPhoto } from "@/content/photos";
import { profile } from "@/content/profile";
import { Section } from "@/components/ui/Section";
import { CopyEmail } from "./CopyEmail";

const links = [
  { label: "LinkedIn", href: profile.links.linkedin, detail: "pushkar-singh-b34b9b341" },
  { label: "GitHub", href: profile.links.github, detail: "PushkarSingh-26" },
  { label: "LeetCode", href: profile.links.leetcode, detail: "Pushkar-26" },
  { label: "Tensortonic", href: profile.links.tensortonic, detail: "pushkarml" },
];

/** The page ends the way a sequence does: with an end-of-text token. */
export function ContactSection() {
  const eot = tokens.special.endoftext;
  return (
    <Section id="contact" label="Contact" pace="loose">
      <div className="wrap grid gap-12 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <Image
            src={portraitPhoto.src}
            alt={portraitPhoto.alt}
            width={224}
            height={224}
            quality={88}
            placeholder="blur"
            className="mb-7 h-[112px] w-[112px] rounded-full object-cover ring-1 ring-rule"
          />
          <h2 className="h-section">Write to me</h2>
          <p className="lead measure mt-5">
            Email is the fastest way to reach me.
          </p>
          <p className="mt-8 text-[clamp(1.25rem,2.6vw,1.75rem)] font-semibold break-all">
            <a className="link" href={`mailto:${profile.email}`}>
              {profile.email}
            </a>
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a className="btn btn-primary" href={`mailto:${profile.email}`}>
              Email me
            </a>
            <CopyEmail email={profile.email} />
            <a className="btn btn-secondary" href={profile.resumePdf} download>
              Download résumé (PDF)
            </a>
          </div>
        </div>

        <div className="lg:col-span-4 lg:col-start-9">
          <h3 className="small text-ink-2">Elsewhere</h3>
          <ul className="mt-3 border-t border-rule">
            {links.map((l) => (
              <li key={l.label} className="border-b border-rule">
                <a
                  className="flex min-h-12 items-baseline justify-between gap-4 py-3 group"
                  href={l.href}
                  target="_blank"
                  rel="noreferrer"
                >
                  <span className="font-semibold group-hover:text-caret">{l.label}</span>
                  <span className="small text-ink-2 truncate">{l.detail}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>

        <div className="lg:col-span-12 mt-6 flex flex-wrap items-center gap-3" aria-hidden="true">
          <span className="tok tok-neutral mono text-ink">{eot.text}</span>
          <span className="mono text-ink-2">{eot.id}</span>
          <span className="small text-ink-2">End of sequence.</span>
        </div>
      </div>
    </Section>
  );
}
