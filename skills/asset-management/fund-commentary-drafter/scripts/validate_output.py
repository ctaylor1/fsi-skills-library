#!/usr/bin/env python3
"""Deterministic output validation for fund-commentary-drafter.

Gate a commentary package before it is handed to a human for external delivery. Enforces:
  1. All required template sections are present and non-empty.
  2. Performance and attribution figures tie out (no un-reconciled numbers).
  3. Claim substantiation: every claim is source-cited and supported; no unsupported claims.
  4. Source/period fidelity: claims carry the package period; no period mismatch.
  5. No prohibited/misleading marketing language (guarantees, "will outperform", etc.).
  6. Required disclosures are present.
  7. Product AND compliance approvals are recorded (approver + date).
  8. Draft-only: delivery_status must not indicate the package was sent/distributed.
  9. The draft-only standing note is present.

Usage: python validate_output.py commentary_package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = ["performance_summary", "attribution", "positioning", "flows",
                     "market_context", "outlook", "disclosures"]
DELIVERED_STATES = {"sent", "submitted", "distributed", "published", "filed", "emailed", "released"}
STANDING_NOTE = ("Draft only - not for distribution until product and compliance approvals "
                 "are recorded; this skill does not send, file, or publish.")
PROHIBITED_PATTERNS = [
    r"\bguarantee(d|s)?\b", r"\brisk[- ]free\b", r"\bcannot lose\b", r"\bno risk of loss\b",
    r"\bwill (out)?perform\b", r"\bassured returns?\b", r"\bpromis(e|es|ed)\b",
    r"\bcan'?t lose\b", r"\bno chance of loss\b", r"\bsafe investment\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or {}
    period_label = (doc.get("period") or {}).get("label", "")

    # 1. required sections present + non-empty
    for s in REQUIRED_SECTIONS:
        sec = sections.get(s)
        if not sec:
            errors.append(f"missing required section: {s}")
            continue
        if s == "disclosures":
            if not (sec.get("disclosures")):
                errors.append("section 'disclosures' is empty")
        elif not sec.get("claim_ids"):
            errors.append(f"section {s!r} has no claims")

    # 2. tie-outs
    tie = doc.get("tie_outs") or {}
    for name in ("performance", "attribution"):
        t = tie.get(name) or {}
        if t.get("ok") is not True:
            errors.append(f"{name} tie-out failed (figures do not tie out): {t.get('detail','no detail')}")

    # 3 + 4. claim substantiation and period fidelity
    ledger = doc.get("claim_ledger") or []
    if not ledger:
        errors.append("claim_ledger is empty (nothing to substantiate)")
    for c in ledger:
        cid = c.get("id", "?")
        if c.get("supported") is not True or not c.get("source_refs"):
            errors.append(f"unsupported claim {cid}: not source-cited/substantiated: {c.get('text','')[:80]!r}")
        pl = c.get("period_label")
        if pl and period_label and pl != period_label:
            errors.append(f"period mismatch on claim {cid}: {pl!r} != package period {period_label!r}")
    if doc.get("unsupported_claims"):
        ids = [u.get("id", "?") for u in doc["unsupported_claims"]]
        errors.append(f"unsupported claim(s) present, must be resolved or removed before release: {ids}")

    # 5. prohibited / misleading language (scan claim narrative only, not approved disclosures)
    scan = " ".join(str(c.get("text", "")) for c in ledger) + " " + str(doc.get("narrative", ""))
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited/misleading marketing language detected: {m.group(0)!r}")

    # 6. required disclosures present
    have = set(doc.get("disclosures_present") or (sections.get("disclosures") or {}).get("disclosures") or [])
    for d in doc.get("required_disclosures") or []:
        if d not in have:
            errors.append(f"required disclosure missing: {d}")

    # 7. approvals recorded (product AND compliance)
    approvals = doc.get("approvals") or {}
    for role in ("product", "compliance"):
        a = approvals.get(role) or {}
        if a.get("status") != "approved":
            errors.append(f"{role} approval not recorded (status={a.get('status')!r}); required before delivery")
        elif not (a.get("approver") and a.get("date")):
            errors.append(f"{role} approval missing approver/date")

    # 8. draft-only: not sent/distributed by this skill
    ds = str(doc.get("delivery_status", "")).lower()
    if ds in DELIVERED_STATES:
        errors.append(f"delivery_status {ds!r} indicates the package was sent/distributed (draft-only violation)")

    # 9. standing note present
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing draft-only standing note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "commentary_package_good.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
