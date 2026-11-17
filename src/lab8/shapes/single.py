"""Shape B — one ReAct agent.

`lab8.runtime.run_react` drives the loop with max_steps=8. `decide` (the model
stand-in) may only pick read tools; the runtime refuses write tools. After the
loop, code — not the model — passes the FULL quote to `durability.issue_refund`.

`decide` quotes from the order row returned by `lookup_order`, never from the
delay or clause written in the ticket, so an overstated ticket cannot raise
the amount. Each decide() call is one MockLLM call so cost stays comparable.

Trace contract v1: every return path goes through `finish()`. The trace logs
tool names and statuses, not the raw observation (which includes the ticket).
"""

from __future__ import annotations

from typing import Any

from lab8.db import connect
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes._flow import early, settle
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _make_decide(claim_id: str, *, seed: int, budget: Budget, trace: Trace):
    """Deterministic policy over read tools. State lives here because run_react
    only hands back the last tool result."""
    state: dict[str, Any] = {"claim": None, "order": None}

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        last_tool = seen.get("last_tool")
        last = seen.get("last_result") or {}
        complete(budget, seed=seed, purpose="react", prompt=f"{claim_id}|after={last_tool or 'start'}")

        if last_tool is None:
            action: dict[str, Any] = {"tool": "get_claim_view", "args": {"claim_id": claim_id}}
        elif last_tool == "get_claim_view":
            state["claim"] = last
            if not last.get("found"):
                action = {"final": {"status": "failed", "error_reason": "unknown_claim"}}
            elif not last.get("order_id"):
                action = {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}
            else:
                action = {
                    "tool": "lookup_order",
                    "args": {"order_id": last["order_id"], "principal_id": last["principal_id"]},
                }
        elif last_tool == "lookup_order":
            if not last.get("visible"):
                action = {"final": {"status": "escalated", "error_reason": last.get("reason")}}
            else:
                state["order"] = last["order"]
                action = {"tool": "compute_compensation", "args": {"order": last["order"]}}
        elif last_tool == "compute_compensation":
            action = {"final": {"status": "quote", "quote": last}}
        else:
            action = {"final": {"status": "failed", "error_reason": f"unexpected_tool:{last_tool}"}}

        trace.add("step", {"tool": action.get("tool"), "final": (action.get("final") or {}).get("status")})
        return action

    return decide, state


def _run(conn, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))
    ctx = dict(shape=SHAPE, claim_id=claim_id, seed=seed, budget=budget, trace=trace)

    decide, state = _make_decide(claim_id, seed=seed, budget=budget, trace=trace)
    loop = run_react(
        conn,
        budget,
        observation={"claim": {"claim_id": claim_id}},
        decide=decide,
        max_steps=MAX_STEPS,
    )
    final = loop["final"]
    trace.add("loop", {"stopped": loop["stopped"]})
    if state["order"] is not None:
        trace.add("order", {"visible": True, "order": state["order"]})

    if loop["stopped"] == "step_cap":
        return early(conn, **ctx, status="failed", reason="step_cap")

    if final["status"] != "quote":
        complete(budget, seed=seed, purpose="draft", prompt=final["status"])
        return early(conn, **ctx, status=final["status"], reason=final.get("error_reason"))

    quote_payload = final["quote"]
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={quote_payload['amount_vnd']}")
    return settle(conn, **ctx, quote_payload=quote_payload, crash_at=crash_at)
