"""Shape C — orchestrator plus read-only investigators.

1. The orchestrator reads the claim view and handles the cases that need no
   investigation (unknown claim, missing order_id).
2. It builds a handoff with `lab8.handoff.make_handoff`: allowlisted fields,
   read-only tools, no parent_secret, raw headers, ticket or claim row in facts.
3. `lab8.runtime.run_readonly_investigators` runs those tools (no write registry).
4. The orchestrator quotes from the investigator's order view and is the only
   caller of `durability.issue_refund`, with the FULL quote.
5. The trace stores the sanitized handoff, never the parent context.

An LLM summary of the parent context is not a sanitizer; the allowlist is.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes._flow import early, settle
from lab8.shapes.common import safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "orchestrator"
INVESTIGATOR_TOOLS = ["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"]


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


def _run(conn, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))
    ctx = dict(shape=SHAPE, claim_id=claim_id, seed=seed, budget=budget, trace=trace)

    # Orchestrator: triage on the claim view.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add("claim", {"found": claim["found"], "has_order_id": bool(claim.get("order_id"))})
    complete(budget, seed=seed, purpose="plan", prompt=f"triage {claim_id}")
    if not claim["found"]:
        return early(conn, **ctx, status="failed", reason="unknown_claim")
    if not claim["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        return early(conn, **ctx, status="needs_info", reason="missing_order_id")

    # Handoff: allowlist only, read-only tools.
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="quote_claim_from_order_row",
        facts={},
        allowed_tools=INVESTIGATOR_TOOLS,
    )
    trace.add("handoff", safe_dump(handoff))

    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim["principal_id"])
    complete(budget, seed=seed, purpose="investigate", prompt=handoff["task"])
    tools = investigated["tools"]
    order_view = tools.get("lookup_order") or {}
    history = tools.get("lookup_refund_history") or {}
    trace.add(
        "investigator",
        {
            "order_visible": bool(order_view.get("visible")),
            "order_reason": order_view.get("reason"),
            "order": order_view.get("order"),
            "refunded_vnd": history.get("refunded_vnd"),
            "policy_count": len((tools.get("lookup_policy") or {}).get("policies") or []),
        },
    )
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return early(conn, **ctx, status="escalated", reason=order_view.get("reason"))

    quote_payload = tools["compute_compensation"]
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={quote_payload['amount_vnd']}")
    return settle(conn, **ctx, quote_payload=quote_payload, crash_at=crash_at)
