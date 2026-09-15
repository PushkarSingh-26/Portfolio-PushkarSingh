export const profile = {
  name: "Pushkar Singh",
  role: "AI/ML engineer",
  statement:
    "I fine-tune and evaluate language models, and build the retrieval, agent and automation systems that put them to work — lately in security operations.",
  principle:
    "The systems I build cite their evidence and get checked before they're trusted — and in AegisAI, no response action runs until a person approves it.",
  email: "pushkar7singh7@gmail.com",
  resumePdf: "/pushkar-singh-resume.pdf",
  links: {
    linkedin: "https://www.linkedin.com/in/pushkar-singh-b34b9b341/",
    github: "https://github.com/PushkarSingh-26",
    leetcode: "https://leetcode.com/u/Pushkar-26/",
    tensortonic: "https://www.tensortonic.com/profile/pushkarml",
  },
  siteUrl: "https://pushkarsingh.vercel.app",
} as const;

export const sources = {
  resume: { label: "Résumé", href: "/pushkar-singh-resume.pdf" },
  aegis: {
    label: "AegisAI repository",
    href: "https://github.com/PushkarSingh-26/cyber-threat-intelligence-platform",
  },
  "paper-agents": {
    label: "AI agents paper",
    href: "https://drive.google.com/file/d/1Q3upBKAYQot7wNx8G0Yqxm8m-QFaNxAo/view",
  },
  "paper-sentiment": {
    label: "Sentiment analysis paper",
    href: "https://drive.google.com/file/d/1gu7O6QmAuryQ17YGT4m1XmjDN9yYrFBb/view",
  },
  "sigma-demo": { label: "sigma-cli output", href: undefined },
  stated: { label: "Provided by Pushkar", href: undefined },
  finance: { label: "Finance Pilot repository", href: "https://github.com/PushkarSingh-26/YFinance-Stockbot" },
  "sentiment-code": { label: "Sentiment paper code", href: "https://github.com/PushkarSingh-26/stock-market-pred-using-LSTM-NLP" },
} as const;
