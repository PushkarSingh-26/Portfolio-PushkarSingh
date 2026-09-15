import { ev, type Evidence } from "./types";

export interface TimelineEntry {
  id: string;
  lane: "work" | "project" | "education";
  title: string;
  org: string;
  /** Decimal years for placement on the axis. `end: null` means ongoing. */
  start: number;
  end: number | null;
  period: string;
  /** Editorial one-liner for the arc. Framing only — facts live in `points`. */
  step?: string;
  roles?: { title: string; period: string }[];
  points: Evidence[];
  capabilities: string[];
  tools: string[];
  href?: string;
  /** The résumé's own title, used on /resume and in the PDF. */
  resumeTitle?: string;
}

export const NOW = 2026 + 8.4 / 12; // mid-September 2026

export const timeline: TimelineEntry[] = [
  {
    id: "globtier",
    lane: "work",
    title: "Machine Learning Engineer Intern",
    org: "Globtier Infotech, Noida",
    start: 2023 + 5 / 12,
    end: 2023 + 7 / 12,
    period: "June – July 2023",
    step: "Classic machine learning, end to end",
    points: [
      ev("resume", "Worked on an end-to-end machine learning project involving data preprocessing, feature engineering, model training, and performance optimization using Python, Pandas, Scikit-learn, and NumPy."),
      ev("resume", "Assisted in evaluating model accuracy and documenting project outcomes for deployment and future enhancements."),
    ],
    capabilities: ["features", "training"],
    tools: ["Python", "Pandas", "Scikit-learn", "NumPy"],
  },
  {
    id: "rento",
    lane: "work",
    title: "Founding AI Application Developer Intern",
    org: "Rento India Marketplace",
    start: 2025 + 2 / 12,
    end: 2025 + 9 / 12,
    period: "Mar – Sept 2025",
    step: "AI inside a product",
    points: [
      ev("resume", "Designed and prototyped the mobile application for the Rento India Marketplace, creating user-centric interfaces for a peer-to-peer rental platform."),
      ev("resume", "Contributed to AI chatbot development and machine learning model implementation using marketplace data to support intelligent recommendations and automated customer assistance."),
    ],
    capabilities: ["chatbots", "recsys", "product"],
    tools: ["Machine learning", "Chatbots"],
  },
  {
    id: "codec",
    lane: "work",
    title: "Product Development Intern, then AI Automation Developer",
    org: "Codec Networks",
    start: 2026,
    end: null,
    period: "Jan 2026 – present",
    step: "LLM systems at work",
    roles: [
      { title: "Product Development Intern", period: "Jan – Apr 2026" },
      { title: "AI Automation Developer", period: "May 2026 – present" },
    ],
    points: [
      ev("resume", "Developed intelligent ISO 27001 compliance automation workflows using n8n for enterprise clients."),
      ev("resume", "Contributed to an AI-powered Managed SOC platform by building a RAG application with pgvector for semantic search across 350+ operational policy documents and implementing Shuffle SOAR integrations for automated security orchestration and incident response."),
    ],
    capabilities: ["rag", "vector-search", "n8n", "soar", "enterprise-automation"],
    tools: ["n8n", "pgvector", "Shuffle SOAR"],
  },
  {
    id: "aegisai",
    lane: "project",
    title: "AegisAI",
    resumeTitle: "AegisAI – Intelligent SOC & Threat Intelligence Platform",
    org: "Project",
    start: 2026 + 5 / 12,
    end: 2026 + 8 / 12,
    period: "June – Aug 2026",
    step: "An AI platform of my own, grounded in evidence",
    points: [
      ev("resume", "Built an AI/ML-powered Cyber Threat Intelligence & Autonomous SOC platform using Python, FastAPI, PostgreSQL, and Neo4j, integrating Wazuh and threat intelligence for automated correlation and enrichment."),
      ev("resume", "Implemented ML risk scoring, graph-based threat analysis, predictive intelligence, AI-driven investigations, autonomous triage, and Shuffle-based SOAR orchestration."),
    ],
    capabilities: ["risk-models", "graph", "grounded-llm", "threat-intel", "soar"],
    tools: ["Python", "FastAPI", "PostgreSQL", "Neo4j", "Wazuh", "Shuffle SOAR"],
    href: "/work/aegisai",
  },
  {
    id: "sigma-llm",
    lane: "project",
    title: "Sigma rule LLM",
    resumeTitle: "Domain-Tuned LLM for Sigma Detection Rules (QLoRA)",
    org: "Project",
    start: 2026 + 7 / 12,
    end: null,
    period: "Aug 2026 – present",
    step: "Training the model itself",
    points: [
      ev("resume", "Fine-tuning an open-weight LLM to generate Sigma detection rules from threat descriptions, trained on the public SigmaHQ corpus with category-level held-out splits."),
      ev("resume", "Built a compiler-based eval harness (sigma-cli) scoring schema validity, backend compilation, and field correctness; benchmarking against base and frontier models in MLflow."),
    ],
    capabilities: ["qlora", "llm-eval"],
    tools: ["QLoRA", "sigma-cli", "MLflow"],
    href: "/work/sigma-llm",
  },
  {
    id: "bca",
    lane: "education",
    title: "Bachelor of Computer Applications",
    org: "Amity University Noida",
    start: 2021 + 6 / 12,
    end: 2024 + 5 / 12,
    period: "2021 – 2024",
    points: [ev("resume", "Bachelor of Computer Applications")],
    capabilities: [],
    tools: [],
  },
  {
    id: "mca",
    lane: "education",
    title: "Master of Computer Applications",
    org: "SRM Institute of Science and Technology, KTR",
    start: 2024 + 6 / 12,
    end: 2026 + 5 / 12,
    period: "2024 – 2026",
    points: [ev("resume", "Master of Computer Application")],
    capabilities: [],
    tools: [],
  },
];

export const education = [
  { degree: "Master of Computer Applications", school: "SRM Institute of Science and Technology, KTR", period: "2024 – 2026", grade: "CGPA 9.67" },
  { degree: "Bachelor of Computer Applications", school: "Amity University Noida", period: "2021 – 2024", grade: "CGPA 7.89" },
];

export const kisanDiary = {
  summary: ev(
    "resume",
    "Developing Kisan Diary, an enterprise-grade Agriculture ERP platform designed for future government deployment, integrating farmer lifecycle management, plot management, secure authentication, digital payments, notifications, and AI-powered automation into a unified, scalable platform.",
  ),
  modules: [
    "Farmer lifecycle management",
    "Plot management",
    "Secure authentication",
    "Digital payments",
    "Notifications",
    "AI-powered automation",
  ],
};
