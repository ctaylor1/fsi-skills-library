#!/usr/bin/env python3
"""Deterministic output validation for model-inventory-maintainer.

Enforces the R3 decision-support guardrails before the inventory change proposal is
presented or handed off:
  1. status is 'proposed' (never posted/approved/final/certified) and requires_adjudication.
  2. computed_materiality_tier ties out to the versioned rubric applied to the recorded
     materiality_tie_out.factors — using the EFFECTIVE thresholds the compute step recorded
     in materiality_tie_out.config (so a configured, non-default rubric ties out to itself),
     falling back to the strict defaults when no config is echoed.
  3. Every finding has >= 1 cited evidence row (non-empty citation) — traceability.
  4. Every reconciliation break is typed from the taxonomy.
  5. No autonomous-decision / posting / approval / attestation / closure / filing language.
  6. The standing disclaimer is present.

Usage:
  python validate_output.py proposal.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

FACTOR_KEYS = ("financial_exposure", "decision_autonomy", "customer_impact", "regulatory_use")
DEFAULT_CONFIG = {"tier1_min": 8, "tier2_min": 4, "escalate_at": 3,
                  "escalating_factors": ["decision_autonomy", "regulatory_use"]}
ALLOWED_STATUS = {"proposed"}
FORBIDDEN_STATUS = {"posted", "approved", "final", "certified", "attested", "closed", "committed"}
BREAK_TYPES = {"value_mismatch", "missing_in_inventory", "missing_in_source", "stale"}
DISCLAIMER = ("Proposed inventory changes and findings only; not an approval, attestation, "
              "or system-of-record update. Model Risk Governance adjudication is required "
              "before any change is posted.")
# Positive autonomous-decision / write assertions an R3 proposal must NOT make:
DECISION_PATTERNS = [
    r"\bposted to the (model )?inventory\b", r"\b(written|committed) to the (system of record|registry)\b",
    r"\brecord (has been|was) (posted|updated|registered)\b", r"\bregistered in the inventory\b",
    r"\bapproved for (production|use|deployment)\b", r"\b(the )?(model|agent) is approved\b",
    r"\bcertif(y|ied|ies)\b", r"\battest(ed|s|ation (is )?complete)\b", r"\bsigned off\b",
    r"\bsign-off (is )?complete\b", r"\bcleared for (use|production)\b",
    r"\bclosed the (finding|gap|issue)\b", r"\bfinding[s]? (are|is) closed\b",
    r"\bno (human |further )?(review|adjudication) (is )?(needed|required)\b",
    r"\bauto-?approv", r"\bhas been decommissioned\b", r"\bwe (have )?filed\b",
]


def _effective_cfg(tie: dict) -> dict:
    """Re-derive the tier with the SAME thresholds the compute step used.

    calculate_or_transform.py resolves cfg = {**DEFAULT_CONFIG, **doc.config} and echoes the
    effective tier thresholds into materiality_tie_out.config. Read those back so a configured
    (non-default) rubric ties out to itself rather than to the hardcoded defaults — otherwise
    a legitimately configured rubric fails its own validation. Missing or malformed values
    fall back to the strict DEFAULT_CONFIG (fail-safe: an absent/garbled echo can only tighten
    the check, never loosen it)."""
    echoed = tie.get("config") if isinstance(tie, dict) else None
    echoed = echoed if isinstance(echoed, dict) else {}
    cfg = dict(DEFAULT_CONFIG)
    for k in ("tier1_min", "tier2_min", "escalate_at"):
        if k in echoed:
            try:
                cfg[k] = int(echoed[k])
            except (TypeError, ValueError):
                pass  # keep the strict default on a malformed threshold
    ef = echoed.get("escalating_factors")
    if isinstance(ef, list) and all(isinstance(x, str) for x in ef):
        cfg["escalating_factors"] = list(ef)
    return cfg


def _expected_tier(factors: dict, cfg: dict) -> str:
    score = sum(int(factors.get(k, 0) or 0) for k in FACTOR_KEYS)
    escalate = any(int(factors.get(k, 0) or 0) >= cfg["escalate_at"]
                   for k in cfg["escalating_factors"])
    if score >= cfg["tier1_min"] or escalate:
        return "Tier 1"
    if score >= cfg["tier2_min"]:
        return "Tier 2"
    return "Tier 3"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []

    # 1. status + adjudication gate
    status = pack.get("status")
    if status in FORBIDDEN_STATUS:
        errors.append(f"forbidden status {status!r} — an R3 proposal is 'proposed', not decided/posted")
    elif status not in ALLOWED_STATUS:
        errors.append(f"status {status!r} not in allowed {sorted(ALLOWED_STATUS)}")
    if pack.get("requires_adjudication") is not True:
        errors.append("requires_adjudication must be true (human adjudication is mandatory)")
    if not (pack.get("adjudication_owner") or "").strip():
        errors.append("missing adjudication_owner")

    # 2. materiality tie-out (re-derive with the rubric config the compute step recorded)
    tie = pack.get("materiality_tie_out") or {}
    factors = tie.get("factors") or {}
    exp_tier = _expected_tier(factors, _effective_cfg(tie))
    if pack.get("computed_materiality_tier") != exp_tier:
        errors.append(f"computed_materiality_tier {pack.get('computed_materiality_tier')!r} != "
                      f"deterministic {exp_tier!r} for factors {factors}")

    # 3. finding evidence traceability
    for f in pack.get("findings") or []:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('id')} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('id')} evidence row missing citation")

    # 4. reconciliation break typing
    for r in pack.get("reconciliation") or []:
        if r.get("result") == "break" or r.get("break_type"):
            bt = r.get("break_type")
            if bt not in BREAK_TYPES:
                errors.append(f"reconciliation break on {r.get('attribute')!r} has invalid "
                              f"break_type {bt!r} (taxonomy: {sorted(BREAK_TYPES)})")

    # 5. no decision/posting/closure/filing language (scan free text + finding descriptions)
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("description", "")) for f in pack.get("findings") or []]
                    + [str(pack.get("lifecycle", {}).get("reason", ""))])
    for pat in DECISION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"autonomous-decision/action language detected: {m.group(0)!r} "
                          f"(R3 proposes; it does not decide/post/close/file)")

    # 6. standing disclaimer
    combined = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in combined:
        errors.append("missing standing disclaimer text")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "proposal_example.json"
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
