import { ev, type ToolGroup } from "./types";

/**
 * The toolkit, in the résumé's own groups, ordered AI-first.
 * Tools with no `links` are listed skills: real, but not tied to a project on this site.
 */
export const toolGroups: ToolGroup[] = [
  {
    id: "genai-tools",
    label: "Generative AI and LLM tools",
    tools: [
      { label: "Transformers (Hugging Face)", links: [] },
      { label: "LangChain", links: [] },
      { label: "LangGraph", links: [] },
      {
        label: "n8n",
        links: [
          { work: "codec", evidence: ev("resume", "Developed intelligent ISO 27001 compliance automation workflows using n8n for enterprise clients.") },
          { work: "paper-agents", evidence: ev("paper-agents", "The experimental implementation was conducted within the n8n automation platform") },
        ],
      },
      { label: "MCP", links: [] },
    ],
  },
  {
    id: "project-stack",
    label: "Model and retrieval stack from my work and papers",
    tools: [
      { label: "QLoRA", links: [{ work: "sigma-llm", evidence: ev("resume", "Domain-Tuned LLM for Sigma Detection Rules (QLoRA)") }] },
      { label: "sigma-cli", links: [{ work: "sigma-llm", evidence: ev("resume", "Built a compiler-based eval harness (sigma-cli)") }] },
      { label: "MLflow", links: [{ work: "sigma-llm", evidence: ev("resume", "benchmarking against base and frontier models in MLflow.") }] },
      { label: "pgvector", links: [{ work: "codec", evidence: ev("resume", "building a RAG application with pgvector for semantic search") }] },
      {
        label: "Pinecone",
        links: [{ work: "paper-agents", evidence: ev("paper-agents", "stored in a vector database (Pinecone)") }],
      },
      {
        label: "OpenAI and Gemini APIs",
        links: [{ work: "paper-agents", evidence: ev("paper-agents", "LLMs (OpenAI GPT, Gemini)") }],
      },
      {
        label: "SerpAPI",
        links: [ { work: "finance-pilot", evidence: ev("finance", "Real-time financial news from SerpAPI with AI-powered summaries", "README.md") },{ work: "paper-agents", evidence: ev("paper-agents", "The Enrichment Layer invokes APIs such as SerpAPI, LinkedIn, and domain-specific scrapers") }],
      },
      { label: "OpenSearch", links: [{ work: "finance-pilot", evidence: ev("finance", "Semantic search using OpenSearch vector database with sentence transformers", "README.md") }] },
      { label: "sentence-transformers", links: [{ work: "finance-pilot", evidence: ev("finance", "self.model = SentenceTransformer('all-MiniLM-L6-v2')", "backend/opensearch_client.py") }] },
      { label: "Plotly", links: [{ work: "finance-pilot", evidence: ev("finance", "Streamlit, Plotly (multiple chart types)", "README.md") }] },
      { label: "NocoDB", links: [{ work: "finance-pilot", evidence: ev("finance", "Save all queries to NocoDB", "README.md") }] },
      { label: "Keras (LSTM)", links: [{ work: "paper-sentiment", evidence: ev("sentiment-code", "from keras.layers import Dense, LSTM, Dropout, Dense, Activation", "notebook-code.py") }] },
      {
        label: "VADER (NLTK)",
        links: [{ work: "paper-sentiment", evidence: ev("paper-sentiment", "Valence Aware Dictionary and Sentiment Reasoner, which is a part of the Natural Language Toolkit (NLTK) library for Python") }],
      },
    ],
  },
  {
    id: "data",
    label: "Data science and analytics",
    tools: [
      { label: "Machine learning", links: [{ work: "globtier", evidence: ev("resume", "Worked on an end-to-end machine learning project") }] },
      { label: "Pandas", links: [ { work: "finance-pilot", evidence: ev("finance", "FastAPI, YFinance, Pandas, SerpAPI", "README.md") },{ work: "globtier", evidence: ev("resume", "using Python, Pandas, Scikit-learn, and NumPy.") }] },
      { label: "NumPy", links: [{ work: "globtier", evidence: ev("resume", "using Python, Pandas, Scikit-learn, and NumPy.") }] },
      { label: "Scikit-learn", links: [ { work: "paper-sentiment", evidence: ev("sentiment-code", "from sklearn.preprocessing import MinMaxScaler", "notebook-code.py") },{ work: "globtier", evidence: ev("resume", "using Python, Pandas, Scikit-learn, and NumPy.") }] },
      { label: "TensorFlow", links: [] },
      { label: "Matplotlib", links: [{ work: "paper-sentiment", evidence: ev("sentiment-code", "import matplotlib.pyplot as plt", "notebook-code.py") }] },
      { label: "yfinance", links: [{ work: "finance-pilot", evidence: ev("finance", "FastAPI, YFinance, Pandas, SerpAPI", "README.md") }] },
      { label: "Seaborn", links: [{ work: "paper-sentiment", evidence: ev("sentiment-code", "import seaborn as sns", "notebook-code.py") }] },
      { label: "Tableau", links: [] },
      { label: "Power BI", links: [] },
    ],
  },
  {
    id: "languages",
    label: "Programming languages",
    tools: [
      {
        label: "Python",
        links: [
          { work: "aegisai", evidence: ev("resume", "platform using Python, FastAPI, PostgreSQL, and Neo4j") },
          { work: "globtier", evidence: ev("resume", "using Python, Pandas, Scikit-learn, and NumPy.") },
          { work: "paper-sentiment", evidence: ev("paper-sentiment", "the Python project programming was carried out on Google Colab using default settings.") },
        ],
      },
      { label: "Java", links: [] },
    ],
  },
  {
    id: "databases",
    label: "Databases",
    tools: [
      { label: "SQL", links: [] },
      {
        label: "PostgreSQL",
        links: [
          { work: "aegisai", evidence: ev("resume", "platform using Python, FastAPI, PostgreSQL, and Neo4j") },
          { work: "paper-agents", evidence: ev("paper-agents", "connects to enterprise repositories (e.g., NocoDB, PostgreSQL, Google Sheets)") },
        ],
      },
      { label: "Neo4j", links: [{ work: "aegisai", evidence: ev("resume", "platform using Python, FastAPI, PostgreSQL, and Neo4j") }] },
      { label: "MongoDB", links: [] },
    ],
  },
  {
    id: "frameworks",
    label: "Tools and frameworks",
    tools: [
      { label: "FastAPI", links: [ { work: "finance-pilot", evidence: ev("finance", "FastAPI, YFinance, Pandas, SerpAPI", "README.md") },{ work: "aegisai", evidence: ev("resume", "platform using Python, FastAPI, PostgreSQL, and Neo4j") }] },
      { label: "REST APIs", links: [] },
      { label: "Streamlit", links: [ { work: "paper-sentiment", evidence: ev("sentiment-code", "This repository contains a Streamlit frontend", "README.md") },{ work: "finance-pilot", evidence: ev("finance", "Streamlit, Plotly (multiple chart types)", "README.md") }] },
      { label: "Gradio", links: [] },
      {
        label: "Google Colab",
        links: [{ work: "paper-sentiment", evidence: ev("paper-sentiment", "the Python project programming was carried out on Google Colab using default settings.") }],
      },
      { label: "Jupyter Notebook", links: [] },
    ],
  },
  {
    id: "security",
    label: "Security platforms",
    tools: [
      { label: "Wazuh", links: [{ work: "aegisai", evidence: ev("resume", "integrating Wazuh and threat intelligence for automated correlation and enrichment.") }] },
      {
        label: "Shuffle SOAR",
        links: [
          { work: "codec", evidence: ev("resume", "implementing Shuffle SOAR integrations for automated security orchestration and incident response.") },
          { work: "aegisai", evidence: ev("resume", "Shuffle-based SOAR orchestration.") },
        ],
      },
      { label: "Digital accessibility testing", links: [] },
      { label: "Configuration audit", links: [] },
    ],
  },
  {
    id: "cloud",
    label: "Cloud and DevOps",
    tools: [
      { label: "AWS (EC2, Lambda, ECS, EKS, RDS, S3, DynamoDB, Aurora, EBS)", links: [] },
      { label: "Azure", links: [] },
      { label: "Terraform (HCL)", links: [] },
      { label: "Jenkins", links: [] },
      { label: "Ansible", links: [] },
      { label: "Git and GitHub", links: [] },
    ],
  },
];

/** Only what the résumé lists. */
export const foreignLanguages = ["German (conversational)"];
