#!/usr/bin/env python3
"""Deterministic output validation for settlement-break-reconciler.

Validates the final reconciliation pack (the calculate_or_transform core + an optional
narrative) before it is presented or delivered. Enforces the Reconcile & validate controls:

  1. Tie-outs      — a tie_out summary is present with numeric per-source totals and the
                     three reconciling differences; every break impact is numeric.
  2. Break taxonomy — every break has a break_type drawn from the documented taxonomy;
                     no unknown types.
  3. Lineage       — every break and every proposed correction cites >= 1 evidence row
                     with a non-empty citation.
  4. Idempotency   — reconciliation_id present; break_ids unique; correction_ids unique and
                     each correction references exactly one existing break.
  5. Proposed-only — every correction has status "proposed" and requires_approval true; NO
                     correction carries a posted/booked/executed status, and the narrative
                     contains no "journal posted / correction applied" language.
  6. Consistency   — reported total_break_impact equals the sum of |break impact|.
  7. Disclaimer    — the standing draft-only disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

BREAK_TYPES = {
    "AMOUNT_MISMATCH_GROSS", "FEE_VARIANCE", "RESERVE_VARIANCE", "NET_CALC_MISMATCH",
    "NET_CASH_MISMATCH", "LEDGER_POSTING_MISMATCH", "MISSING_IN_BANK",
    "MISSING_IN_LEDGER", "MISSING_IN_SETTLEMENT", "DUPLICATE", "CURRENCY_MISMATCH",
}
TIE_OUT_FIELDS = (
    "network_gross_total", "processor_gross_total", "processor_net_total",
    "bank_cash_total", "ledger_net_total", "net_diff_bank_minus_processor",
    "net_diff_ledger_minus_processor",
)
DISCLAIMER = (
    "Reconciliation and proposed corrections only; no journal has been posted and no system "
    "of record has been changed. Every proposed correction requires human review and "
    "approval before posting."
)
# A correction is a PROPOSAL. These states mean it was actually actioned — forbidden at R2.
FORBIDDEN_STATUSES = {"posted", "booked", "executed", "submitted", "applied", "settled", "completed"}
# Narrative language asserting a correction was actioned (draft-only skill must not do this).
POSTING_PATTERNS = [
    r"\bposted (the |a )?(journal|correction|entry|adjustment|je)\b",
    r"\bbooked (the |a )?(correction|journal|entry|adjustment)\b",
    r"\bcorrections? (have been|has been|were|was) (posted|applied|booked|executed|made)\b",
    r"\bposted to the (ledger|gl|general ledger|system of record)\b",
    r"\bwe (posted|booked|executed|submitted|applied)\b",
    r"\bentry has been posted\b",
    r"\bapplied the correction\b",
]
_num = (int, float)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    breaks = pack.get("breaks")
    if breaks is None:
        errors.append("missing 'breaks' list")
        breaks = []
    corrections = pack.get("corrections") or []

    # 1. tie-outs
    tie = pack.get("tie_out")
    if not isinstance(tie, dict):
        errors.append("missing 'tie_out' summary")
    else:
        for f in TIE_OUT_FIELDS:
            if f not in tie:
                errors.append(f"tie_out missing field '{f}'")
            elif not isinstance(tie[f], _num):
                errors.append(f"tie_out['{f}'] must be numeric, got {tie[f]!r}")

    # 2 + 3. break taxonomy + lineage
    break_ids: list = []
    for b in breaks:
        bid = b.get("break_id")
        break_ids.append(bid)
        if b.get("break_type") not in BREAK_TYPES:
            errors.append(f"break {bid}: unknown break_type {b.get('break_type')!r}")
        if not isinstance(b.get("impact"), _num):
            errors.append(f"break {bid}: impact must be numeric, got {b.get('impact')!r}")
        ev = b.get("evidence") or []
        if not ev:
            errors.append(f"break {bid}: no evidence rows (lineage required)")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"break {bid}: evidence row missing citation")

    # 4. idempotency
    if not pack.get("reconciliation_id"):
        errors.append("missing reconciliation_id (reproducibility/idempotency)")
    if len(break_ids) != len(set(break_ids)):
        errors.append("duplicate break_id(s) — breaks must be uniquely identified")
    corr_ids = [c.get("correction_id") for c in corrections]
    if len(corr_ids) != len(set(corr_ids)):
        errors.append("duplicate correction_id(s) — corrections must be idempotent/unique")
    break_id_set = set(break_ids)
    for c in corrections:
        ref = c.get("break_ref")
        if ref not in break_id_set:
            errors.append(f"correction {c.get('correction_id')}: break_ref {ref!r} not a known break")

    # 5. proposed-only corrections
    for c in corrections:
        cid = c.get("correction_id")
        status = str(c.get("status", "")).lower()
        if status != "proposed":
            errors.append(f"correction {cid}: status must be 'proposed', got {c.get('status')!r}")
        if status in FORBIDDEN_STATUSES:
            errors.append(f"correction {cid}: forbidden actioned status {status!r} (R2 proposes, never posts)")
        if c.get("requires_approval") is not True:
            errors.append(f"correction {cid}: requires_approval must be true")
        ev = c.get("evidence") or []
        if not ev:
            errors.append(f"correction {cid}: no evidence rows (lineage required)")

    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]).lower()
    for pat in POSTING_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"posting/actioned language detected: {m.group(0)!r} (skill is draft-only; corrections are proposed)")

    # 6. impact consistency
    summ = pack.get("summary") or {}
    if "total_break_impact" in summ:
        expect = round(sum(abs(b["impact"]) for b in breaks if isinstance(b.get("impact"), _num)), 2)
        if round(float(summ["total_break_impact"]), 2) != expect:
            errors.append(f"summary.total_break_impact {summ['total_break_impact']} != sum|impact| {expect}")

    # 7. disclaimer
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing draft-only disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
