import { gateMessages, mockExecution, recommendation, type GateAction, type RecStatus } from "@/content/aegis";

/*
  A browser-only simulation of backend/app/response_engine.py. Same states, same
  guards, same refusal messages (mapped to HTTP 409 by the router). Nothing here
  talks to a server.
*/

export const ACTOR = "analyst (you)";
export const REC_ID = 1;

export interface AuditRow {
  seq: number;
  time: string;
  rec: number;
  event: "generated" | "approved" | "rejected" | "executed" | "verified" | "failed";
  from: RecStatus | null;
  to: RecStatus;
  actor: string;
}

export interface Reply {
  seq: number;
  action: GateAction;
  code: 200 | 409;
  body: string;
}

export interface ExecutionResult {
  provider: "mock";
  ticket_id: string;
  status: "created";
  simulated: true;
}

export interface Verification {
  verified: boolean;
  provider: string;
  reference: string;
  checked_at: string;
}

export interface SimState {
  status: RecStatus;
  generated: boolean;
  audit: AuditRow[];
  reply: Reply | null;
  execution: ExecutionResult | null;
  verification: Verification | null;
  seq: number;
}

export type SimAction =
  | { type: "generate"; time: string }
  | { type: "act"; action: GateAction; time: string; iso: string }
  | { type: "reset"; time: string };

export const initialSim: SimState = {
  status: "pending",
  generated: false,
  audit: [],
  reply: null,
  execution: null,
  verification: null,
  seq: 0,
};

/** Which status each call requires, and where it leads. */
const REQUIRES: Record<GateAction, RecStatus> = {
  approve: "pending",
  reject: "pending",
  execute: "approved",
  verify: "executed",
};
const LEADS_TO: Record<GateAction, RecStatus> = {
  approve: "approved",
  reject: "rejected",
  execute: "executed",
  verify: "verified",
};

const generatedRow = (seq: number, time: string): AuditRow => ({
  seq,
  time,
  rec: REC_ID,
  event: "generated",
  from: null,
  to: "pending",
  actor: "system",
});

export function simReducer(s: SimState, a: SimAction): SimState {
  switch (a.type) {
    case "generate": {
      if (s.generated) return s;
      const seq = s.seq + 1;
      return { ...s, generated: true, seq, audit: [generatedRow(seq, a.time)] };
    }
    case "reset": {
      const seq = s.seq + 1;
      return { ...initialSim, generated: true, seq, audit: [generatedRow(seq, a.time)] };
    }
    case "act": {
      const seq = s.seq + 1;
      if (s.status !== REQUIRES[a.action]) {
        // Refused: PermissionError → 409. No state change, so nothing is audited.
        return {
          ...s,
          seq,
          reply: { seq, action: a.action, code: 409, body: JSON.stringify({ detail: gateMessages[a.action](s.status) }) },
        };
      }
      const to = LEADS_TO[a.action];
      const row: AuditRow = { seq, time: a.time, rec: REC_ID, event: to as AuditRow["event"], from: s.status, to, actor: ACTOR };
      let execution = s.execution;
      let verification = s.verification;
      let body: Record<string, unknown> = { id: REC_ID, status: to };
      if (a.action === "approve" || a.action === "reject") body = { ...body, approved_by: ACTOR };
      if (a.action === "execute") {
        execution = { provider: "mock", ticket_id: mockExecution.ticketId, status: "created", simulated: true };
        body = { ...body, execution_result: execution };
      }
      if (a.action === "verify") {
        verification = { verified: true, provider: "mock", reference: mockExecution.ticketId, checked_at: a.iso };
        body = { ...body, verified: true };
      }
      return {
        ...s,
        seq,
        status: to,
        audit: [...s.audit, row],
        reply: { seq, action: a.action, code: 200, body: JSON.stringify(body) },
        execution,
        verification,
      };
    }
  }
}

export const recTitle = JSON.parse(recommendation.fields.find((f) => f.key === "title")!.value) as string;
