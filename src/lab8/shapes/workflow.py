"""Shape A — deterministic workflow.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Fixed steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> `needs_info`. No ledger write.
3. `lookup_order`. Not visible -> `escalated`. Only allowlisted order fields are kept.
4. Quote from the order row. Delay numbers written in the ticket are ignored.
5. Quote 0 -> `denied`, issue_refund is not called.
6. Quote > 0 -> `durability.issue_refund(conn, claim_id, <full quote>, crash_at=crash_at)`.
   The host checks approval and the per-order cap. InjectedCrash is not caught.
7. MockLLM only drafts the reply text; it never chooses the amount or commits.

Trace contract v1: every return path goes through `finish()`, which writes
{"run_id", "events"} for this run. The trace never holds the ticket, the
principal id, parent_secret, or raw order rows.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"

# Shared tail (early/settle). single.py and orchestrator.py import these from here:
# the grader copies only the three shape files, so no extra helper module may exist.


def early(
    conn: sqlite3.Connection,
    *,
    shape: str,
    claim_id: str,
    seed: int,
    budget: Budget,
    trace: Trace,
    status: str,
    reason: str | None,
) -> RunResult:
    """Return without touching the ledger (needs_info / escalated / failed)."""
    trace.add("decision", {"status": status, "reason": reason})
    return finish(
        conn,
        shape=shape,
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=0,
        budget=budget,
        trace=trace,
        error_reason=reason,
    )


def settle(
    conn: sqlite3.Connection,
    *,
    shape: str,
    claim_id: str,
    seed: int,
    budget: Budget,
    trace: Trace,
    quote_payload: dict[str, Any],
    crash_at: str | None,
) -> RunResult:
    proposal = int(quote_payload["amount_vnd"])
    trace.add(
        "quote",
        {
            "amount_vnd": proposal,
            "reason": quote_payload.get("reason"),
            "clause_ids": list(quote_payload.get("clause_ids") or []),
        },
    )

    if proposal <= 0:
        return early(
            conn,
            shape=shape,
            claim_id=claim_id,
            seed=seed,
            budget=budget,
            trace=trace,
            status="denied",
            reason=quote_payload.get("reason"),
        )

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        # Flush what we know, then let the crash propagate (T12 checks it fires).
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if outcome["ok"]:
        status, reason = "resolved", None
    elif outcome["conflict"]:
        status, reason = "failed", outcome["reason"]
    else:
        status, reason = "denied", outcome["reason"]
    trace.add("host", {"ok": bool(outcome["ok"]), "reason": outcome["reason"]})
    trace.add("decision", {"status": status, "reason": reason})
    return finish(
        conn,
        shape=shape,
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=reason,
    )


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

    # 1. Claim view (allowlisted columns only).
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add("claim", {"found": claim["found"], "has_order_id": bool(claim.get("order_id"))})
    if not claim["found"]:
        return early(conn, **ctx, status="failed", reason="unknown_claim")

    # 2. Missing order -> ask the customer.
    if not claim["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        return early(conn, **ctx, status="needs_info", reason="missing_order_id")

    # 3. Order inside the principal's scope.
    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
    trace.add("order", {"visible": order_view["visible"], "reason": order_view["reason"], "order": order_view.get("order")})
    if not order_view["visible"]:
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return early(conn, **ctx, status="escalated", reason=order_view["reason"])

    # 4. Quote from the order row, never from the ticket text.
    budget.add_tool(tool_cost())
    quote_payload = compute_compensation(conn, order_view["order"])
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={quote_payload['amount_vnd']}")

    # 5-6. Deny on zero, otherwise let the host write.
    return settle(conn, **ctx, quote_payload=quote_payload, crash_at=crash_at)
