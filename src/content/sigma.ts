import { ev } from "./types";

export const sigmaProject = {
  title: "A domain-tuned LLM for Sigma detection rules",
  status: "In progress since August 2026. Benchmark results aren't published yet.",
  question:
    "Can an open-weight model, tuned on public Sigma rules, write rules that compile and use the right fields — for rule categories it never saw in training?",
  summary: ev(
    "resume",
    "Fine-tuning an open-weight LLM to generate Sigma detection rules from threat descriptions, trained on the public SigmaHQ corpus with category-level held-out splits. Built a compiler-based eval harness (sigma-cli) scoring schema validity, backend compilation, and field correctness; benchmarking against base and frontier models in MLflow.",
  ),
};

export type SigmaStageId = "data" | "qlora" | "model" | "rule" | "compiler" | "validation" | "benchmark";

export const sigmaStages: {
  id: SigmaStageId;
  name: string;
  title: string;
  body: string;
  evidence: ReturnType<typeof ev>;
}[] = [
  {
    id: "data",
    name: "Data",
    title: "Public rules, split by category",
    body: "Training data comes from the public SigmaHQ rule corpus. Whole categories of rules are held out, so the test set asks for rules in categories the model never trained on — memorizing the corpus doesn't help.",
    evidence: ev("resume", "trained on the public SigmaHQ corpus with category-level held-out splits."),
  },
  {
    id: "qlora",
    name: "QLoRA",
    title: "Fine-tuning with QLoRA",
    body: "QLoRA keeps the base model's weights frozen in quantized form and trains small low-rank adapters on top, so a capable open-weight model can be tuned on modest hardware.",
    evidence: ev("resume", "Domain-Tuned LLM for Sigma Detection Rules (QLoRA)"),
  },
  {
    id: "model",
    name: "Model",
    title: "An open-weight model, tuned for one job",
    body: "The model is being tuned to read a plain-language threat description and write a Sigma rule for it.",
    evidence: ev("resume", "Fine-tuning an open-weight LLM to generate Sigma detection rules from threat descriptions"),
  },
  {
    id: "rule",
    name: "Generated rule",
    title: "A rule, written token by token",
    body: "The output is a YAML Sigma rule: a log source, one or more selections, and a condition that combines them. Generation is the easy part; the question is whether the rule is right.",
    evidence: ev("resume", "generate Sigma detection rules from threat descriptions"),
  },
  {
    id: "compiler",
    name: "Compiler",
    title: "Every rule goes through sigma-cli",
    body: "Instead of judging rules by eye, the harness hands each one to sigma-cli, which parses it and compiles it into a real backend query.",
    evidence: ev("resume", "Built a compiler-based eval harness (sigma-cli)"),
  },
  {
    id: "validation",
    name: "Validation",
    title: "Three checks, each catching something different",
    body: "Schema validity asks whether the rule is well-formed Sigma. Backend compilation asks whether it becomes a working query. Field correctness asks whether it looks at the right fields — a rule can compile and still watch the wrong thing.",
    evidence: ev("resume", "scoring schema validity, backend compilation, and field correctness"),
  },
  {
    id: "benchmark",
    name: "Benchmark",
    title: "Same harness, three kinds of model",
    body: "The tuned model, its untuned base model and frontier models all go through the same checks, and benchmark runs are tracked in MLflow. The comparison is the result — and it isn't in yet.",
    evidence: ev("resume", "benchmarking against base and frontier models in MLflow."),
  },
];

export const sigmaChecks = [
  { id: "schema", name: "Schema validity", question: "Is it well-formed Sigma?" },
  { id: "compile", name: "Backend compilation", question: "Does it compile to a query?" },
  { id: "fields", name: "Field correctness", question: "Does it use the right fields?" },
] as const;

export const benchmarkRows = ["Fine-tuned model", "Base model", "Frontier models"];
