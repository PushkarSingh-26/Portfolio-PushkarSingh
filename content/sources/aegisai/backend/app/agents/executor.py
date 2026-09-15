"""Plan executor (Phase 14.1).

Runs a planner task graph: resolves "$placeholder" params from a running context
built out of earlier tool outputs, invokes each vetted tool, logs every call
(auditable), and collects evidence. Tool failures degrade to skipped/error steps
without aborting the investigation.
"""

import logging
import time

from sqlalchemy.orm import Session

from backend.app.agents.tools import run_tool

log = logging.getLogger("agents.executor")

_CONTEXT_KEYS = ("cve_id", "technique_id", "actor_id", "actor_name", "campaign_id")


def _update_context(ctx: dict, data) -> None:
    if not isinstance(data, dict):
        return
    scopes = [data]
    if isinstance(data.get("findings"), dict):
        scopes.append(data["findings"])
    if isinstance(data.get("evidence"), dict):
        scopes.append(data["evidence"])
    nested_ev = (data.get("findings") or {}).get("evidence") if isinstance(data.get("findings"), dict) else None
    if isinstance(nested_ev, dict):
        scopes.append(nested_ev)

    for scope in scopes:
        for k in _CONTEXT_KEYS:
            if scope.get(k) and k not in ctx:
                ctx[k] = scope[k]
        if scope.get("techniques") and "technique_id" not in ctx:
            ctx["technique_id"] = scope["techniques"][0]
        if scope.get("threat_actors") and "actor_name" not in ctx:
            ctx["actor_name"] = scope["threat_actors"][0]
        if scope.get("related_cves") and "cve_id" not in ctx:
            ctx["cve_id"] = scope["related_cves"][0]


def _resolve(params: dict, ctx: dict):
    resolved, missing = {}, []
    for key, val in params.items():
        if isinstance(val, str) and val.startswith("$"):
            ref = val[1:]
            if ctx.get(ref) is not None:
                resolved[key] = ctx[ref]
            else:
                missing.append(ref)
        else:
            resolved[key] = val
    return resolved, missing


def execute(plan: list[dict], db: Session) -> tuple[dict, list, dict]:
    context: dict = {}
    evidence: dict = {}
    tool_calls: list = []

    for s in plan:
        params, missing = _resolve(s["params"], context)
        if missing:
            tool_calls.append({"step": s["step"], "tool": s["tool"], "params": s["params"],
                               "status": "skipped", "summary": f"unresolved {missing}",
                               "rationale": s["rationale"]})
            continue
        t0 = time.perf_counter()
        result = run_tool(s["tool"], db, params)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        tool_calls.append({"step": s["step"], "tool": s["tool"], "params": params,
                           "status": "ok" if result.get("ok") else "error",
                           "summary": result.get("summary", ""), "duration_ms": ms,
                           "rationale": s["rationale"]})
        evidence[f"{s['step']}_{s['tool']}"] = result
        if result.get("ok"):
            _update_context(context, result.get("data"))

    return evidence, tool_calls, context
