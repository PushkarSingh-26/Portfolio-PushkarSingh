import { ev, type Evidence } from "./types";

export interface Paper {
  slug: string;
  title: string;
  /** The résumé's own label for it. */
  label: string;
  authors: string[];
  affiliation: string;
  pdf: string;
  /** Public repository with the paper's code, when there is one. */
  code?: string;
  question: Evidence;
  approach: Evidence;
  keywords: string[];
}

export const agentsPaper = {
  slug: "ai-agents-corporate-workload",
  title: "Introducing AI Agents for Automating Corporate Workload",
  label: "Research paper",
  authors: ["Pushkar Singh", "Aditya Pawar", "Saurav Kumar Shukla", "Dr. R. Reena Rose"],
  affiliation: "SRM Institute of Science and Technology, KTR",
  pdf: "https://drive.google.com/file/d/1Q3upBKAYQot7wNx8G0Yqxm8m-QFaNxAo/view",
  /** No public repository for this paper. */
  code: undefined as string | undefined,
  question: ev(
    "paper-agents",
    "Low-Code/No-Code (LCNC) platforms have emerged as a means to democratize automation by allowing non-technical users to design workflows, yet they remain constrained in handling unstructured data, cross-domain complexity, and context-driven decision making.",
  ),
  approach: ev(
    "paper-agents",
    "Unlike existing LCNC solutions, our approach enables autonomous yet collaborative agents that leverage large language models (LLMs), retrieval-augmented generation (RAG), and API connectors within orchestrated workflows.",
  ),
  keywords: ["AI agents", "n8n", "LLMs", "RAG", "Vector database", "Multi-agent systems"],
  layers: [
    { id: "ingest", name: "Data ingestion and triggering", evidence: ev("paper-agents", "Captures raw data from multiple sources including web reviews, candidate resumes, LinkedIn APIs, spreadsheets, CRM systems, and form submissions.") },
    { id: "process", name: "Processing and enrichment", evidence: ev("paper-agents", "Performs data preprocessing tasks such as splitting, filtering, normalization, and entity extraction.") },
    { id: "core", name: "AI core", evidence: ev("paper-agents", "The reasoning layer, where specialized domain agents operate.") },
    { id: "orchestrate", name: "Automation and orchestration", evidence: ev("paper-agents", "Implements end-to-end automation through n8n, managing workflow triggers, system integrations, notification pipelines, and task scheduling.") },
    { id: "act", name: "Action and visualization", evidence: ev("paper-agents", "Produces actionable outputs in the form of dashboards, structured data updates (Google Sheets, CRM), QuickChart visualizations, and real-time communication (email, SMS, Telegram).") },
  ],
  /** Cells follow the paper's own per-agent experimental setup (Section IV.C), one per layer. */
  agents: [
    {
      id: "hr",
      name: "HR assistant",
      cells: {
        ingest: ev("paper-agents", "Candidate resumes (PDFs), LinkedIn APIs, recruiter Telegram inputs."),
        process: ev("paper-agents", "Resumes converted into embeddings via OpenAI models; enriched with LinkedIn data; stored in Pinecone."),
        core: ev("paper-agents", "Candidate ranking, automated interview question generation via RAG pipelines."),
        orchestrate: ev("paper-agents", "Recruiter updates via Telegram; results stored in CRM."),
        act: ev("paper-agents", "Candidate shortlists, interview scheduling, recruiter notifications."),
      },
    },
    {
      id: "sales",
      name: "Sales and research agent",
      cells: {
        ingest: ev("paper-agents", "Google Sheets lead lists, SerpAPI for company data, LinkedIn API."),
        process: ev("paper-agents", "Iterative reasoning for lead scoring and enrichment."),
        core: ev("paper-agents", "Personalized outreach message generation using OpenAI LLMs."),
        orchestrate: ev("paper-agents", "Email workflows, CRM record updates, optional manual review for high-value leads."),
        act: ev("paper-agents", "Ranked leads, automated prospect emails, enriched CRM entries."),
      },
    },
    {
      id: "data",
      name: "Data analysis agent",
      cells: {
        ingest: ev("paper-agents", "Natural language queries (chat triggers), connected to NocoDB/PostgreSQL."),
        process: ev("paper-agents", "Mapping query terms to database schema; comparative analytics."),
        core: ev("paper-agents", "Reasoning agent interprets queries, executes data lookups, generates charts via QuickChart."),
        orchestrate: ev("paper-agents", "Workflow orchestration in n8n for query execution and chart delivery."),
        act: ev("paper-agents", "Real-time data insights visualized as charts, dashboards, and structured text summaries."),
      },
    },
    {
      id: "feedback",
      name: "Customer feedback agent",
      cells: {
        ingest: ev("paper-agents", "Web review scrapers, form submissions."),
        process: ev("paper-agents", "Feedback split into single statements, normalized."),
        core: ev("paper-agents", "Sentiment classification (positive/neutral/negative) and theme extraction."),
        orchestrate: ev("paper-agents", "Alerts triggered on negative sentiment thresholds, stored in Google Sheets."),
        act: ev("paper-agents", "Trend dashboards, automated email/SMS alerts, aggregated customer insights."),
      },
    },
  ],
  sharedBackbone: ev(
    "paper-agents",
    "While each domain agent functions independently, they share a common orchestration backbone through n8n, which manages workflow triggers, scheduling, and inter-agent data flows.",
  ),
  humanInLoop: ev("paper-agents", "Optional manual review steps allow human-in-the-loop validation for high-value accounts."),
  /** Table 4 of the paper, transcribed from the figure. Shown only with attribution. */
  reportedTimes: [
    { domain: "HR recruitment", manual: "25–30 min per candidate", automated: "7–9 min", reduction: "70–75%", evidence: ev("paper-agents", "HR Recruitment | 25–30 min per candidate | 7–9 min | 70–75%") },
    { domain: "Sales research", manual: "20 min per lead", automated: "5–7 min", reduction: "65–75%", evidence: ev("paper-agents", "Sales Research | 20 min per lead | 5–7 min | 65–75%") },
    { domain: "Data analysis", manual: "15 min per query", automated: "3–5 min", reduction: "65–80%", evidence: ev("paper-agents", "Data Analysis | 15 min per query | 3–5 min | 65–80%") },
    { domain: "Sentiment analysis", manual: "12 min per dataset", automated: "3 min", reduction: "75%", evidence: ev("paper-agents", "Sentiment Analysis | 12 min per dataset | 3 min | 75%") },
  ],
};

export const sentimentPaper = {
  slug: "sentiment-stock-prediction",
  title: "Integrating Sentiment Analysis from Financial News for Enhanced Stock Market Prediction",
  label: "Research publication",
  authors: ["Pushkar Singh", "Shuchi Sethi"],
  affiliation: "Amity Institute of Information Technology, Amity University Noida",
  pdf: "https://drive.google.com/file/d/1gu7O6QmAuryQ17YGT4m1XmjDN9yYrFBb/view",
  code: "https://github.com/PushkarSingh-26/stock-market-pred-using-LSTM-NLP",
  question: ev(
    "paper-sentiment",
    "This research aims to investigate the connection between sentiment analysis and stock market forecasting, analyzing how sentiments expressed in news articles influence market dynamics to improve prediction accuracy.",
  ),
  approach: ev(
    "paper-sentiment",
    "Research on stock market prediction involves combining LSTM, a type of neural network capable of processing sequential data, with NLP techniques to analyze textual data from source which is financial news.",
  ),
  keywords: ["Stock market prediction", "LSTM", "Sentiment analysis"],
  /** The paper's methodology flowchart (Figure 2), in order. */
  steps: [
    { id: "collect", name: "Collect prices and headlines", detail: "BSE Sensex prices and Indian news headlines, loaded from CSV", evidence: ev("paper-sentiment", "stock_headlines = pd.read_csv('/content/drive/MyDrive/final-india-news-headlines.csv')") },
    { id: "clean", name: "Clean", detail: "Duplicates, missing values and data types", evidence: ev("paper-sentiment", "In Python, numerous data cleaning techniques are available, including removing duplicates, managing missing values, and converting data types.") },
    { id: "combine", name: "Combine", detail: "Prices and headlines joined by date", evidence: ev("paper-sentiment", "The stock data is merged using the concat command") },
    { id: "vader", name: "Score sentiment with VADER", detail: "Positive, negative, neutral and compound scores per headline", evidence: ev("paper-sentiment", "it provides scores that might be positive, negative, neutral, or compound.") },
    { id: "eda", name: "Explore", detail: "Structure, types and missing values", evidence: ev("paper-sentiment", "Inspection of the dataset reveals its structure, including the data types of each column and any missing values present.") },
    { id: "prepare", name: "Prepare", detail: "Scaled features, date-ordered train/test split", evidence: ev("paper-sentiment", "for time series data like stock prices which is dependent on date, the dataset is divided into train and test dataset in a different way") },
    { id: "model", name: "Train an LSTM", detail: "Stacked LSTM layers with dropout and a dense output", evidence: ev("paper-sentiment", "The developed LSTM model is trained on historical data to predict future market trends") },
    { id: "evaluate", name: "Evaluate", detail: "Error metrics on the held-out period", evidence: ev("paper-sentiment", "Common metrics used for evaluation include mean absolute error (MAE), mean squared error (MSE), or root mean squared error (RMSE), which measure the accuracy of the predictions") },
  ],
  split: ev("paper-sentiment", "Number of rows and columns in the Training set X: (1964, 7) and y: (1964, 1)"),
  splitTest: ev("paper-sentiment", "Number of rows and columns in the Test set X: (490, 7) and y: (490, 1)"),
  sampleRow: {
    date: "2001-01-05",
    headline: "Light combat craft takes India into club class...",
    compound: 0.9253,
    negative: 0.104,
    neutral: 0.744,
    positive: 0.152,
    evidence: ev("paper-sentiment", "headline_text: Light combat craft takes India into club class... | compound 0.9253 | negative 0.104 | neutral 0.744 | positive 0.152"),
  },
  /**
   * The model as written in the published notebook (ntcc_project.ipynb). The paper
   * describes the layer pattern but not the sizes; these come from the code.
   */
  model: {
    input: { text: "7 input features: price, volume and VADER sentiment scores, each read as a step", evidence: ev("sentiment-code", "cols = ['close_price', 'compound', 'compound_shifted', 'volume', 'open_price', 'high', 'low']", "notebook-code.py") },
    target: { text: "The next day's closing price", evidence: ev("sentiment-code", "close_price_shifted = close_price.shift(-1)", "notebook-code.py") },
    layers: [
      { kind: "lstm", spec: "LSTM(100, tanh)", note: "returns sequences" },
      { kind: "dropout", spec: "Dropout(0.1)" },
      { kind: "lstm", spec: "LSTM(100, tanh)", note: "returns sequences" },
      { kind: "dropout", spec: "Dropout(0.1)" },
      { kind: "lstm", spec: "LSTM(100, tanh)" },
      { kind: "dropout", spec: "Dropout(0.1)" },
      { kind: "dense", spec: "Dense(1)", note: "one value out" },
    ],
    layersEvidence: ev("sentiment-code", "model.add(LSTM(100,return_sequences=True,activation='tanh',input_shape=(len(cols),1)))", "notebook-code.py"),
    training: [
      { label: "Loss", value: "mean squared error" },
      { label: "Optimizer", value: "Adam" },
      { label: "Epochs", value: "10" },
      { label: "Batch size", value: "8" },
      { label: "Validation", value: "20% of training rows" },
    ],
    trainingEvidence: ev("sentiment-code", "model.fit(X_train, y_train, validation_split=0.2, epochs=10, batch_size=8, verbose=1)", "notebook-code.py"),
    compileEvidence: ev("sentiment-code", "model.compile(loss='mse' , optimizer='adam')", "notebook-code.py"),
    scaling: { text: "Features and target scaled to the range −1 to 1", evidence: ev("sentiment-code", "scaler_x = preprocessing.MinMaxScaler (feature_range=(-1, 1))", "notebook-code.py") },
  },
  /** The repository's notebook is a separate run from the one reported in the paper. */
  codeRunSplit: ev("sentiment-code", "Number of rows and columns in the Training set X: (3913, 7) and y: (3913, 1)", "notebook-text.txt"),
  codeRunSplitTest: ev("sentiment-code", "Number of rows and columns in the Test set X: (977, 7) and y: (977, 1)", "notebook-text.txt"),
  explorer: ev("sentiment-code", "This repository contains a Streamlit frontend (`app.py`) that implements EDA and sentiment analysis flows based on `ntcc_project.ipynb`.", "README.md"),
  vaderScale: ev("paper-sentiment", "Compound | [-1,1] | Calculates the sum of all lexicon ratings which have been normalized between [-1,1]"),
};

export const papers = [agentsPaper, sentimentPaper];
