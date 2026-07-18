#!/usr/bin/env python3
"""Deterministic output validation for transaction-reconciliation-helper.

Validates the final reconciliation pack (the calculate_or_transform core + a narrative)
before it is presented or delivered. Checks the Reconcile & validate archetype guardrails:

  1. Break taxonomy — every break/routed break carries a break_type in the documented set.
  2. Lineage — every break has >= 1 evidence row and each row carries a citation.
  3. Tie-out — declared control totals recompute deterministically:
        target_total  == source_totals[target_source]
        residual_before == target_total - ledger_total
        net_proposed    == sum(ledger_delta of proposed ledger_adjustments)
        residual_after  == residual_before - net_proposed
  4. Routing — routed settlement/cash-ledger breaks go to settlement-break-reconciler and
     carry NO proposed ledger entry (the helper never resolves settlement-file breaks).
  5. Proposed-only (the R2 hard boundary) — every proposed entry has status "proposed", and
     no posting/finalization language appears anywhere in the pack.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

BREAK_TYPES = {
    "missing_record", "unmatched", "amount_mismatch", "duplicate",
    "status_mismatch", "currency_mismatch", "timing_difference", "fee_variance",
}
ROUTE_SKILL = "settlement-break-reconciler"
DISCLAIMER = ("Proposed entries only; not posted to any system of record. "
              "Human approval and posting required.")
BAD_STATUS = {"posted", "booked", "final", "finalized", "finalised", "approved", "committed"}
# Posting / finalization assertions an R2 draft-only reconciler must never make:
POSTING_PATTERNS = [
    r"\bposted (the |a |an )?(journal|entr|adjustment|correction)", r"\bposted to (the )?(general ledger|gl|ledger)\b",
    r"\bpost(ing|ed)? to the system of record\b", r"\bjournal (has been |was )?posted\b",
    r"\bentr(y|ies) (have|has) been (posted|booked)\b", r"\bbooked to (the )?(gl|general ledger|ledger)\b",
    r"\bledger (has been |was )?updated\b", r"\bwritten to (the )?(system of record|ledger|gl)\b",
    r"\bwrote to (the )?(ledger|gl|system of record)\b", r"\bcommitted to (the )?(ledger|gl|system of record)\b",
    r"\bwe (have )?posted\b", r"\bfinaliz(e|ed) the (entr|adjustment|reconciliation and post)",
    r"\bapproved and posted\b", r"\bentry booked\b",
]


def _r2(x) -> float:
    return round(float(x), 2)


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    breaks = pack.get("breaks") or []
    routed = pack.get("routed_breaks") or []
    proposed = pack.get("proposed_entries") or []
    tie = pack.get("tie_out") or {}
    tol = float(tie.get("tolerance", 0.01))

    # 1 + 2: taxonomy + lineage for transaction-level breaks
    for b in breaks:
        ref = b.get("txn_ref", "?")
        if b.get("break_type") not in BREAK_TYPES:
            errors.append(f"break {ref} has break_type {b.get('break_type')!r} not in taxonomy")
        ev = b.get("evidence") or []
        if not ev:
            errors.append(f"break {ref} has no evidence (lineage required)")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"break {ref} evidence row missing citation")
        pe = b.get("proposed_entry")
        if pe is None:
            errors.append(f"break {ref} has no proposed_entry")

    # 3: tie-out recomputation
    st = tie.get("source_totals") or {}
    tsrc = tie.get("target_source")
    if tsrc is not None and tsrc not in st:
        errors.append(f"tie-out: target_source {tsrc!r} not in source_totals")
    else:
        exp_target = _r2(st.get(tsrc, 0.0))
        if abs(_r2(tie.get("target_total", 0.0)) - exp_target) > tol:
            errors.append(f"tie-out: target_total {tie.get('target_total')} != source_totals[{tsrc!r}] {exp_target}")
    exp_before = _r2(_r2(tie.get("target_total", 0.0)) - _r2(tie.get("ledger_total", 0.0)))
    if abs(_r2(tie.get("residual_before", 0.0)) - exp_before) > tol:
        errors.append(f"tie-out: residual_before {tie.get('residual_before')} != target_total - ledger_total {exp_before}")
    exp_net = _r2(sum(p.get("ledger_delta", 0.0) for p in proposed if p.get("type") == "ledger_adjustment"))
    if abs(_r2(tie.get("net_proposed", 0.0)) - exp_net) > tol:
        errors.append(f"tie-out: net_proposed {tie.get('net_proposed')} != sum(proposed ledger deltas) {exp_net}")
    exp_after = _r2(_r2(tie.get("residual_before", 0.0)) - _r2(tie.get("net_proposed", 0.0)))
    if abs(_r2(tie.get("residual_after", 0.0)) - exp_after) > tol:
        errors.append(f"tie-out: residual_after {tie.get('residual_after')} != residual_before - net_proposed {exp_after}")

    # 4: routing of settlement/cash-ledger breaks
    for rb in routed:
        ref = rb.get("txn_ref", "?")
        if rb.get("route_to") != ROUTE_SKILL:
            errors.append(f"routed break {ref} route_to {rb.get('route_to')!r} != {ROUTE_SKILL!r}")
        if rb.get("proposed_entry") is not None:
            errors.append(f"routed settlement break {ref} must not carry a proposed ledger entry "
                          f"(route to {ROUTE_SKILL})")
        if not (rb.get("evidence") or []):
            errors.append(f"routed break {ref} has no evidence (lineage required)")

    # 5: proposed-only (hard boundary) — status + posting language
    for pe in proposed:
        s = str(pe.get("status", "")).lower()
        if s != "proposed":
            errors.append(f"proposed entry {pe.get('txn_ref')} not marked status='proposed' "
                          f"(got {pe.get('status')!r}) — helper proposes only, never posts")
        if s in BAD_STATUS:
            errors.append(f"proposed entry {pe.get('txn_ref')} carries finalized status {pe.get('status')!r}")
    for b in breaks:
        pe = b.get("proposed_entry") or {}
        if str(pe.get("status", "proposed")).lower() != "proposed":
            errors.append(f"break {b.get('txn_ref')} proposed_entry status {pe.get('status')!r} != 'proposed'")

    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(b.get("reason", "")) for b in breaks]
    text_parts += [str(p.get("narrative", "")) for p in proposed]
    text_parts += [str(rb.get("reason", "")) for rb in routed]
    text = " ".join(text_parts)
    for pat in POSTING_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"posting/finalization language detected: {m.group(0)!r} "
                          f"(helper proposes entries; it never posts)")

    # 6: standing disclaimer
    hay = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in hay:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "recon_pack_example.json"
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
