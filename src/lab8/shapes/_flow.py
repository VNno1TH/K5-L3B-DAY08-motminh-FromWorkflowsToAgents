"""Shared tail for the student shapes: quote -> host write -> RunResult.

Money is decided by `compute_compensation` (code), and the only writer is
`durability.issue_refund` (host). Shapes pass the FULL quote; the host checks
approval, the per-order cap, and idempotency.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, RunResult
from lab8.shapes.common import finish
from lab8.trace import Trace


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
