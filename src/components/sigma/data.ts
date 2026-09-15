import demoJson from "@/content/generated/sigma-demo.json";
import tokensJson from "@/content/generated/tokens.json";

/**
 * Typed view of the real sigma-cli outputs (src/content/generated/sigma-demo.json)
 * and the real o200k_base token strings for the example rule. Nothing here is
 * invented: every string shown by the Sigma components comes from these files.
 */

export type CheckId = "schema" | "compile" | "fields";

export interface CliCheck {
  pass: boolean;
  exitCode: number;
  output: string;
}

export interface FieldCheck {
  pass: boolean;
  used: string[];
  expected: string[];
  missing: string[];
  unexpected: string[];
}

export interface Variant {
  id: string;
  label: string;
  change: string | null;
  yaml: string;
  checks: { schema: CliCheck; compile: CliCheck; fields: FieldCheck };
}

export const tooling = demoJson.tooling;
export const fieldCheckMethod: string = demoJson.fieldCheckMethod;
export const threatDescription: string = demoJson.threatDescription;
export const variants: Variant[] = demoJson.variants;

export const allPass = (v: Variant) => v.checks.schema.pass && v.checks.compile.pass && v.checks.fields.pass;

/** The reference rule is the one that passes every check (derived, not looked up by id). */
export const reference: Variant = variants.find(allPass) ?? variants[0];

/** Real token strings for the valid example rule. */
export const referenceTokens: string[] = tokensJson.sigmaRuleTokens.valid;

/** The rule's file name, as used in the real commands. */
export const ruleFileName: string = tooling.checkCommand.split(" ").pop() ?? "";

export const toolingLine = `sigma-cli ${tooling.sigmaCli}, pySigma ${tooling.pySigma}, Splunk backend ${tooling.splunkBackend}`;

/** The compiled query is the last line of sigma convert's real output. */
export function compiledQuery(v: Variant): string {
  const lines = v.checks.compile.output.split("\n").filter((l) => l.trim().length > 0);
  return lines[lines.length - 1] ?? "";
}

export function commandFor(id: CheckId): string | null {
  if (id === "schema") return tooling.checkCommand;
  if (id === "compile") return tooling.convertCommand;
  return null;
}
