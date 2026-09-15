import { ev, type Area, type Evidence } from "./types";

/**
 * Finance Pilot (repo: YFinance-Stockbot). Everything below is taken from the
 * repository's README and code, which were downloaded into
 * content/sources/finance-pilot and are checked at build time.
 */
export const financePilot = {
  title: "Finance Pilot",
  repo: "https://github.com/PushkarSingh-26/YFinance-Stockbot",
  repoName: "YFinance-Stockbot",
  summary:
    "A stock-market assistant you question in plain language. It reads live Yahoo Finance data, answers with Gemini, and draws the chart the question calls for.",
  summaryEvidence: ev("finance", "Natural language queries powered by Google Gemini 2.0 Flash", "README.md"),

  stack: [
    { label: "Gemini 2.0 Flash", area: "llm" as Area, evidence: ev("finance", "model = genai.GenerativeModel('gemini-2.0-flash-exp')", "backend/main.py") },
    { label: "OpenSearch", area: "genai" as Area, evidence: ev("finance", "Semantic search using OpenSearch vector database with sentence transformers", "README.md") },
    { label: "sentence-transformers", area: "genai" as Area, evidence: ev("finance", "self.model = SentenceTransformer('all-MiniLM-L6-v2')", "backend/opensearch_client.py") },
    { label: "FastAPI", area: null, evidence: ev("finance", "FastAPI, YFinance, Pandas, SerpAPI", "README.md") },
    { label: "yfinance", area: null, evidence: ev("finance", "FastAPI, YFinance, Pandas, SerpAPI", "README.md") },
    { label: "Pandas", area: null, evidence: ev("finance", "FastAPI, YFinance, Pandas, SerpAPI", "README.md") },
    { label: "SerpAPI", area: null, evidence: ev("finance", "Real-time financial news from SerpAPI with AI-powered summaries", "README.md") },
    { label: "Plotly", area: null, evidence: ev("finance", "Streamlit, Plotly (multiple chart types)", "README.md") },
    { label: "Streamlit", area: null, evidence: ev("finance", "Streamlit, Plotly (multiple chart types)", "README.md") },
    { label: "NocoDB", area: null, evidence: ev("finance", "Save all queries to NocoDB", "README.md") },
  ],

  /** Also in the product, shown as a plain list. */
  extras: [
    { text: "News summaries from SerpAPI results", evidence: ev("finance", "Real-time financial news from SerpAPI with AI-powered summaries", "README.md") },
    { text: "Live S&P 500, Dow Jones and NASDAQ overview", evidence: ev("finance", "Live market indices (S&P 500, Dow Jones, NASDAQ) with performance tracking", "README.md") },
    { text: "Every query saved to NocoDB", evidence: ev("finance", "save_to_nocodb(request.question, request.ticker or \"\", result)", "backend/main.py") },
  ],
};

export interface RouteStep {
  text: string;
  evidence: Evidence;
  /** Tint for steps where a model does the work. */
  area?: Area;
}

export interface Route {
  id: "single" | "compare" | "market";
  tab: string;
  example: string;
  /** True when the example is quoted from the README's own example questions. */
  exampleFromReadme: boolean;
  steps: RouteStep[];
  output: { label: string; charts?: string[]; note?: string };
}

/** The three paths a question can take through parse_question_enhanced() in backend/main.py. */
export const routes: Route[] = [
  {
    id: "single",
    tab: "One stock",
    example: "How has this stock performed this year?",
    exampleFromReadme: true,
    steps: [
      {
        text: "yfinance pulls the ticker's price history, company info and dividends",
        evidence: ev("finance", "dividends = stock_data[\"dividends\"]", "backend/main.py"),
      },
      {
        text: "Gemini writes the answer and names the chart to draw",
        area: "llm",
        evidence: ev("finance", "CHART_TYPE: [type]", "backend/main.py"),
      },
      {
        text: "Only chart names on an allow-list are accepted",
        evidence: ev("finance", "valid_types = [\"candlestick\", \"line\", \"volume\", \"bar\", \"none\"]", "backend/main.py"),
      },
      {
        text: "If the Gemini call fails, keyword rules answer instead",
        evidence: ev("finance", "return analyze_without_gemini(question, stock_data)", "backend/main.py"),
      },
    ],
    output: { label: "One of 4 single-stock charts, or none", charts: ["Candlestick", "Line", "Volume", "Dividend bars"] },
  },
  {
    id: "compare",
    tab: "Several stocks",
    example: "Compare AAPL vs GOOGL",
    exampleFromReadme: true,
    steps: [
      {
        text: "Two or more tickers are found in the question itself",
        evidence: ev("finance", "if len(detected_tickers) >= 2:", "backend/main.py"),
      },
      {
        text: "Keyword rules read the wording and pick the comparison chart",
        evidence: ev("finance", "if any(word in q_lower for word in [\"compare\", \"vs\", \"versus\", \"difference between\"]):", "backend/main.py"),
      },
      {
        text: "yfinance fetches data for every ticker named",
        evidence: ev("finance", "# Fetch data for all tickers", "backend/main.py"),
      },
    ],
    output: {
      label: "One of 6 multi-stock charts",
      charts: ["Price comparison", "Performance comparison", "Volume comparison", "Metrics comparison", "Scatter", "Correlation heatmap"],
    },
  },
  {
    id: "market",
    tab: "The market",
    example: "What's happening in the market?",
    exampleFromReadme: false,
    steps: [
      {
        text: "Routed here when it asks about the market and names no ticker",
        evidence: ev("finance", "general_keywords = [\"market\", \"stocks\", \"which\", \"better\", \"what's happening\"]", "backend/main.py"),
      },
      {
        text: "Hybrid search — vector and keyword — over news articles in OpenSearch",
        area: "genai",
        evidence: ev("finance", "Hybrid search combining vector and keyword search", "backend/opensearch_client.py"),
      },
      {
        text: "Embeddings come from all-MiniLM-L6-v2, 384 dimensions",
        area: "genai",
        evidence: ev("finance", "\"dimension\": 384,  # all-MiniLM-L6-v2 dimension", "backend/opensearch_client.py"),
      },
      {
        text: "Gemini answers from the retrieved articles and live stock data",
        area: "llm",
        evidence: ev("finance", "context = \"You are a financial analyst with access to real-time data and news.\\n\\n\"", "backend/main.py"),
      },
    ],
    output: { label: "A written answer grounded in retrieved news", note: "No chart on this path" },
  },
];

export const chartCountEvidence = ev("finance", "def create_dividend_chart(data):", "frontend/components/charts.py");
