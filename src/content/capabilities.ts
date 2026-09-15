import { ev, type Area, type Capability } from "./types";

export const areas: { id: Area; label: string; short: string }[] = [
  { id: "llm", label: "Large language models", short: "LLMs" },
  { id: "genai", label: "Generative AI", short: "Generative AI" },
  { id: "ml", label: "Machine learning", short: "Machine learning" },
  { id: "applied", label: "Applied AI", short: "Applied AI" },
];

/**
 * Capability → work links. Every link carries the sentence that backs it.
 * Nothing here is inferred: if a source doesn't say it, there's no link.
 */
export const capabilities: Capability[] = [
  // ---------- LLMs ----------
  {
    id: "qlora",
    label: "Fine-tuning with QLoRA",
    area: "llm",
    links: [
      {
        work: "sigma-llm",
        evidence: ev(
          "resume",
          "Fine-tuning an open-weight LLM to generate Sigma detection rules from threat descriptions, trained on the public SigmaHQ corpus with category-level held-out splits.",
        ),
      },
    ],
  },
  {
    id: "llm-eval",
    label: "LLM evaluation",
    area: "llm",
    links: [
      {
        work: "sigma-llm",
        evidence: ev(
          "resume",
          "Built a compiler-based eval harness (sigma-cli) scoring schema validity, backend compilation, and field correctness; benchmarking against base and frontier models in MLflow.",
        ),
      },
    ],
  },
  {
    id: "grounded-llm",
    label: "Grounded LLM analysis",
    area: "llm",
    links: [
      {
        work: "aegisai",
        evidence: ev("aegis", "with no LLM configured it returns deterministic, evidence-only answers", "docs/ai_analyst.md"),
      },
    ],
  },
  {
    id: "llm-apis",
    label: "LLM APIs: OpenAI, Gemini",
    area: "llm",
    links: [
      {
        work: "finance-pilot",
        evidence: ev("finance", "Natural language queries powered by Google Gemini 2.0 Flash", "README.md"),
      },
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "The backend integrates multiple AI and ML components such as OpenAI GPT-based models, Google Gemini, and sentiment analysis models."),
      },
    ],
  },

  // ---------- Generative AI ----------
  {
    id: "rag",
    label: "Retrieval-augmented generation",
    area: "genai",
    links: [
      {
        work: "finance-pilot",
        evidence: ev("finance", "Hybrid search combining vector and keyword search", "backend/opensearch_client.py"),
      },
      {
        work: "codec",
        evidence: ev(
          "resume",
          "Contributed to an AI-powered Managed SOC platform by building a RAG application with pgvector for semantic search across 350+ operational policy documents",
        ),
      },
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "It further generates context-specific interview questions through a RAG-based query mechanism, which ensures alignment between the candidate's profile and the job description."),
      },
    ],
  },
  {
    id: "agents",
    label: "AI agents",
    area: "genai",
    links: [
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "we propose a novel framework that integrates AI-driven multi-agent systems with LCNC orchestration using the n8n environment."),
      },
      {
        work: "aegisai",
        evidence: ev("aegis", "The agent acts only through a 12-tool read-only registry over existing services;", "README.md"),
      },
    ],
  },
  {
    id: "human-in-loop",
    label: "Human-in-the-loop control",
    area: "genai",
    links: [
      {
        work: "aegisai",
        evidence: ev("aegis", "Nothing executes automatically: attempting to execute an unapproved recommendation returns HTTP 409.", "README.md"),
      },
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "Optional manual review steps allow human-in-the-loop validation for high-value accounts."),
      },
    ],
  },
  {
    id: "vector-search",
    label: "Embeddings and vector search",
    area: "genai",
    links: [
      {
        work: "finance-pilot",
        evidence: ev("finance", "self.model = SentenceTransformer('all-MiniLM-L6-v2')", "backend/opensearch_client.py"),
      },
      {
        work: "codec",
        evidence: ev("resume", "building a RAG application with pgvector for semantic search across 350+ operational policy documents"),
      },
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "Incoming resumes are first pre-processed into structured embeddings using OpenAI models, stored in a vector database (Pinecone), and linked with candidate metadata"),
      },
    ],
  },
  {
    id: "chatbots",
    label: "Conversational AI",
    area: "genai",
    links: [
      {
        work: "finance-pilot",
        evidence: ev("finance", "Ask any question about stocks, investing, or market analysis", "README.md"),
      },
      {
        work: "rento",
        evidence: ev("resume", "Contributed to AI chatbot development and machine learning model implementation using marketplace data to support intelligent recommendations and automated customer assistance."),
      },
    ],
  },
  {
    id: "n8n",
    label: "Workflow automation with n8n",
    area: "genai",
    links: [
      {
        work: "codec",
        evidence: ev("resume", "Developed intelligent ISO 27001 compliance automation workflows using n8n for enterprise clients."),
      },
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "Implements end-to-end automation through n8n, managing workflow triggers, system integrations, notification pipelines, and task scheduling."),
      },
    ],
  },

  // ---------- Machine learning ----------
  {
    id: "features",
    label: "Feature engineering",
    area: "ml",
    links: [
      {
        work: "globtier",
        evidence: ev("resume", "Worked on an end-to-end machine learning project involving data preprocessing, feature engineering, model training, and performance optimization using Python, Pandas, Scikit-learn, and NumPy."),
      },
      {
        work: "paper-sentiment",
        evidence: ev("paper-sentiment", "feature engineering techniques are employed to generate new informative features."),
      },
    ],
  },
  {
    id: "training",
    label: "Model training and evaluation",
    area: "ml",
    links: [
      {
        work: "globtier",
        evidence: ev("resume", "Assisted in evaluating model accuracy and documenting project outcomes for deployment and future enhancements."),
      },
      {
        work: "paper-sentiment",
        evidence: ev("paper-sentiment", "The developed LSTM model is trained on historical data to predict future market trends"),
      },
    ],
  },
  {
    id: "risk-models",
    label: "Risk scoring models",
    area: "ml",
    links: [
      {
        work: "aegisai",
        evidence: ev("resume", "Implemented ML risk scoring, graph-based threat analysis, predictive intelligence"),
      },
    ],
  },
  {
    id: "graph",
    label: "Graph analytics",
    area: "ml",
    links: [
      {
        work: "aegisai",
        evidence: ev("resume", "Built an AI/ML-powered Cyber Threat Intelligence & Autonomous SOC platform using Python, FastAPI, PostgreSQL, and Neo4j"),
      },
    ],
  },
  {
    id: "nlp",
    label: "NLP and sentiment analysis",
    area: "ml",
    links: [
      {
        work: "paper-sentiment",
        evidence: ev("paper-sentiment", "In this report, the VADER technique is utilized for its capability to not only classify the data sentiments as negative, neutral, or positive but also evaluate the overall sentiment of a sentence"),
      },
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "The AI Core Layer classifies sentiment polarity (positive, neutral, negative) and applies topic modelling for theme extraction"),
      },
    ],
  },
  {
    id: "recsys",
    label: "Recommendation models",
    area: "ml",
    links: [
      {
        work: "rento",
        evidence: ev("resume", "machine learning model implementation using marketplace data to support intelligent recommendations"),
      },
    ],
  },

  // ---------- Applied AI ----------
  {
    id: "secops",
    label: "Security operations",
    area: "applied",
    links: [
      {
        work: "aegisai",
        evidence: ev("resume", "Built an AI/ML-powered Cyber Threat Intelligence & Autonomous SOC platform"),
      },
      {
        work: "codec",
        evidence: ev("resume", "Contributed to an AI-powered Managed SOC platform"),
      },
      {
        work: "sigma-llm",
        evidence: ev("resume", "Fine-tuning an open-weight LLM to generate Sigma detection rules from threat descriptions"),
      },
    ],
  },
  {
    id: "threat-intel",
    label: "Threat intelligence",
    area: "applied",
    links: [
      {
        work: "aegisai",
        evidence: ev("resume", "integrating Wazuh and threat intelligence for automated correlation and enrichment."),
      },
    ],
  },
  {
    id: "soar",
    label: "SOAR orchestration",
    area: "applied",
    links: [
      {
        work: "codec",
        evidence: ev("resume", "implementing Shuffle SOAR integrations for automated security orchestration and incident response."),
      },
      {
        work: "aegisai",
        evidence: ev("resume", "autonomous triage, and Shuffle-based SOAR orchestration."),
      },
    ],
  },
  {
    id: "enterprise-automation",
    label: "Enterprise automation",
    area: "applied",
    links: [
      {
        work: "paper-agents",
        evidence: ev("paper-agents", "The framework unifies automation across four critical corporate domains"),
      },
      {
        work: "codec",
        evidence: ev("resume", "Developed intelligent ISO 27001 compliance automation workflows using n8n for enterprise clients."),
      },
    ],
  },
  {
    id: "product",
    label: "Product engineering",
    area: "applied",
    links: [
      {
        work: "kisan",
        evidence: ev("resume", "Developing Kisan Diary, an enterprise-grade Agriculture ERP platform designed for future government deployment"),
      },
      {
        work: "rento",
        evidence: ev("resume", "Designed and prototyped the mobile application for the Rento India Marketplace, creating user-centric interfaces for a peer-to-peer rental platform."),
      },
    ],
  },
];
