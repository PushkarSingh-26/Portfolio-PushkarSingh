import type { Metadata, Viewport } from "next";
import { Mona_Sans, Martian_Mono } from "next/font/google";
import "./globals.css";
import { MotionProvider } from "@/components/motion/MotionProvider";
import { ContextBar } from "@/components/nav/ContextBar";
import { SiteFooter } from "@/components/nav/SiteFooter";
import { profile } from "@/content/profile";

const mona = Mona_Sans({
  subsets: ["latin"],
  axes: ["wdth"],
  variable: "--font-mona",
  display: "swap",
});

const martian = Martian_Mono({
  subsets: ["latin"],
  axes: ["wdth"],
  variable: "--font-martian",
  display: "swap",
});

const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_PROJECT_PRODUCTION_URL
    ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
    : "http://localhost:3000");

const description =
  "Pushkar Singh is an AI/ML engineer working on LLM fine-tuning, evaluation, retrieval and agents — building AI systems that cite their evidence, get evaluated before they're trusted, and keep people in charge of response actions.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: `${profile.name} — ${profile.role}`, template: `%s` },
  description,
  authors: [{ name: profile.name }],
  openGraph: {
    type: "website",
    title: `${profile.name} — AI/ML engineer`,
    description,
    siteName: profile.name,
  },
  twitter: { card: "summary_large_image", title: `${profile.name} — AI/ML engineer`, description },
};

export const viewport: Viewport = {
  themeColor: "#f3f5f7",
  colorScheme: "light",
};

// Decides before first paint whether the hero's merge animation should play:
// once per session, never with reduced motion. Without JS the hero renders final.
const heroGate = `try{if(!matchMedia('(prefers-reduced-motion: reduce)').matches&&!sessionStorage.getItem('hero-played')&&location.pathname==='/'){document.documentElement.dataset.hero='play'}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${mona.variable} ${martian.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: heroGate }} />
      </head>
      <body>
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <MotionProvider>
          <ContextBar />
          <main id="main" tabIndex={-1} className="outline-none">
            {children}
          </main>
          <SiteFooter />
        </MotionProvider>
      </body>
    </html>
  );
}
