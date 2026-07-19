#!/usr/bin/env python3
"""Deterministic output validation for portfolio-proposal-comparator.

Validates the final comparison pack (the calculate_or_transform core + a narrative) before
it is presented or delivered. Fails closed on any control miss. Checks:
  1. Each proposal's total_cost_bps ties out to expense_weighted_bps + advisory_fee_bps.
  2. Every flag has >= 1 cited evidence row.
  3. A non-empty assumptions block is present (transparent-assumptions requirement).
  4. adjudication_required is true (R3 mandatory human adjudication).
  5. No proposal-selection field carries a value (comparator never picks a winner).
  6. No decision / recommendation / advice / trade-execution / filing language in the
     narrative, flag reasons, or adjudication items.
  7. The standing disclaimer is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = (
    "Comparison and evidence only; not investment, tax, or suitability advice and not a "
    "recommendation to select any proposal. A licensed human must review before any client "
    "discussion or action; no trade has been placed and no system of record has been updated."
)

# Fields that would encode a selection/recommendation the R3 comparator must never make.
SELECTION_FIELDS = ("recommended_proposal", "selected_proposal", "chosen_proposal",
                    "preferred_proposal", "suitable_proposal", "best_proposal", "winner")

# Affirmative decision / recommendation / advice / action language (the disclaimer is stripped
# before scanning, so its negated phrasing does not self-trip).
DECISION_PATTERNS = [
    r"\bwe recommend\b", r"\bi recommend\b",
    r"\brecommend(s|ed|ing)?\s+(that\s+you|proposal|option|choosing|selecting|going with)\b",
    r"\brecommended (proposal|option|choice)\b",
    r"\byou should (choose|select|pick|buy|sell|invest|move|switch|go with|proceed)\b",
    r"\bthe (best|right|preferred|superior) (proposal|option|choice)\b",
    r"\bbest (proposal|option|choice) (is|for)\b",
    r"\bproposal [a-z] is (better|best|superior|preferable|the winner)\b",
    r"\bselect(s|ed|ing)? (a |the |any )?proposal\b", r"\bchoose proposal\b",
    r"\bgo with proposal\b", r"\bproceed with proposal\b",
    r"\b(is|are|looks?|seems?) suitable\b",
    r"\bsuitab(ility|le) (is )?(met|satisfied|approved|confirmed|determined)\b",
    r"\bapprove(d|s)?\s+(the\s+)?(proposal|recommendation|trade|order|comparison)\b",
    r"\bplace (the |these )?trades?\b", r"\bexecute (the |these )?trades?\b",
    r"\bplace (the )?order\b", r"\bfile (the|a) (paperwork|form|report|order|filing)\b",
    r"\bclose (the )?case\b", r"\bwe guarantee\b", r"\bis guaranteed to\b",
    r"\bour (recommendation|advice) is\b", r"\badvise(s|d)? (you|the client|the advisor) to\b",
]


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    proposals = pack.get("proposals") or []
    if len(proposals) < 2:
        errors.append("fewer than 2 proposals in pack (comparison requires >= 2)")
    for p in proposals:
        m = p.get("metrics") or {}
        pid = p.get("proposal_id", "?")
        if all(k in m for k in ("total_cost_bps", "expense_weighted_bps", "advisory_fee_bps")):
            expect = float(m["expense_weighted_bps"]) + float(m["advisory_fee_bps"])
            if abs(float(m["total_cost_bps"]) - expect) > 0.01:
                errors.append(f"proposal {pid} total_cost_bps {m['total_cost_bps']} != "
                              f"expense_weighted+advisory {round(expect, 4)}")

    for f in pack.get("flags") or []:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"flag {f.get('flag')} ({f.get('proposal_id')}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"flag {f.get('flag')} ({f.get('proposal_id')}) evidence row missing citation")

    assumptions = pack.get("assumptions") or {}
    if not (assumptions.get("config") or assumptions.get("notes")):
        errors.append("assumptions block missing or empty (transparent assumptions required)")

    if pack.get("adjudication_required") is not True:
        errors.append("adjudication_required must be true (R3 mandatory human adjudication)")

    for k in SELECTION_FIELDS:
        if pack.get(k):
            errors.append(f"proposal-selection field present: {k}={pack.get(k)!r} "
                          f"(comparator must not select or recommend a proposal)")

    narrative = str(pack.get("narrative", "")).replace(DISCLAIMER, " ")
    text = " ".join([narrative, str(pack.get("notes", ""))]
                    + [str(f.get("reason", "")) for f in pack.get("flags") or []]
                    + [str(x) for x in pack.get("adjudication_items") or []])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"decision/advice language detected: {m.group(0)!r} "
                          f"(R3 comparator evidences and compares, it does not decide/select/advise)")

    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer text")

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
