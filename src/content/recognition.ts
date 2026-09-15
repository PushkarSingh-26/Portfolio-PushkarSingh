import { ev } from "./types";

/** Straight from the résumé. Ordered by year, newest first, résumé order within a year. */
export const achievements = [
  {
    event: "National Level Machine Learning Datathon",
    organizer: "IntellectA",
    year: 2025,
    result: "Best Innovation Award",
    evidence: ev("resume", "National Level Machine Learning Datathon by IntellectA, 2025 - Best Innovation Award Winner"),
  },
  {
    event: "UST Global Sight 2.0 Competition",
    organizer: "",
    year: 2025,
    result: "Top 25",
    evidence: ev("resume", "UST Global Sight 2.0 Competition, 2025 - Top 25"),
  },
  {
    event: "SRM Project Expo",
    organizer: "",
    year: 2025,
    result: "Special Category Award",
    evidence: ev("resume", "SRM Project Expo 2025 - Special Category award Winner"),
  },
  {
    event: "PAN India Web Scraping Challenge",
    organizer: "S.A. College of Arts & Science",
    year: 2025,
    result: "Bronze certificate",
    evidence: ev("resume", "PAN India Web Scraping Challenge by S.A. College of Arts & Science, 2025 - Bronze Certificate"),
  },
  {
    event: "TECHZOOM",
    organizer: "SRM IST, KTR",
    year: 2025,
    result: "1st runner-up",
    evidence: ev("resume", "TECHZOOM organized by SRM IST, KTR, 2025 - 1st Runner Up"),
  },
  {
    event: "INFINITRIX project presentation",
    organizer: "Loyola College, Chennai",
    year: 2024,
    result: "1st runner-up",
    evidence: ev("resume", "INFINITRIX, Project Presentation, Loyola college, Chennai, 2024 - 1st Runner Up"),
  },
];

export const leadership: {
  title: string;
  org: string;
  period?: string;
  evidence: ReturnType<typeof ev>;
  summary?: string;
}[] = [
  {
    title: "President, LiveWires Club",
    org: "SRM",
    period: "July 2025 – July 2026",
    evidence: ev("resume", "Led the club’s transition in to an innovation-driven, enterprise-oriented organization; managed diverse teams and drove new initiatives."),
    summary: "Led the club’s move to an innovation-driven, enterprise-oriented organization; managed diverse teams and drove new initiatives.",
  },
  {
    title: "Vice President, Sports Department",
    org: "AIIT, Amity University",
    period: "Sept 2023 – May 2024",
    evidence: ev("resume", "Coordinated and motivated sports teams for major inter-university events, promoting teamwork, discipline, and high performance."),
    summary: "Coordinated and motivated sports teams for major inter-university events.",
  },
  {
    title: "Head member, Placement Committee",
    org: "SRM IST, KTR",
    evidence: ev("stated", "Placement Committee head member (SRM IST, KTR)."),
  },
  {
    title: "Discipline and Sports member, Directorate of Student Affairs",
    org: "SRM IST, KTR",
    evidence: ev("stated", "Directorate of Student Affairs (DSA) Discipline and Sports member. (SRM IST, KTR)."),
  },
];

/**
 * Sport and esports. Kept apart from the technical competitions so neither
 * list dilutes the other.
 */
export const beyondWork = {
  karate: {
    title: "Karate",
    medals: [
      { label: "National gold", count: 4 },
      { label: "State gold", count: 3 },
      { label: "State silver", count: 2 },
    ],
    evidence: ev("stated", "KARATE – 4 NATIONALS GOLD Medals, 3 STATE GOLD Medals, 2 STATE SILVER Medals"),
  },
  esports: {
    title: "ESL India CoC, powered by Snapdragon",
    result: "1st runner-up",
    evidence: ev("stated", "1st Runner Up at ESL (Electronic Sports League) INDIA COC powered by SNAPDRAGON."),
  },
};
