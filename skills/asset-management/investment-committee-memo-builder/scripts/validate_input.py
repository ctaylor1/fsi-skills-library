#!/usr/bin/env python3
"""Deterministic input validation for investment-committee-memo-builder.

Validates an IC-memo build request before assembly. Fails closed on structural problems
(so the skill never drafts on top of a malformed request); warns on data-quality gaps that
force a `needs-data` disposition or that must be disclosed to the committee.

Input schema (JSON): see references/source-map.md. Key fields:
  template_version, deal{deal_id,name,strategy,recommended_action}, sources[{source_id,
  type,ref,approved}], model{source_id,entry{ev,metric_value,net_debt,entry_multiple,
  equity_check},leverage{total_debt,ebitda,leverage_x},returns{moic,irr,hold_years}},
  valuation{...,source_id}, scenarios[{name,moic,irr,source_id}], risks[{risk,mitigant,
  source_id}], sizing{proposed_commitment,fund_nav,position_pct,single_name_limit_pct,...,
  source_id}, thesis_points[{claim,source_id}], decision_questions[], approvals[{role,status}]

Usage: python validate_input.py ic_request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("template_version", "deal", "sources", "model", "scenarios", "valuation",
                "risks", "sizing", "thesis_points", "decision_questions", "approvals")
REQUIRED_DEAL = ("deal_id", "name", "strategy", "recommended_action")
RECOMMENDATIONS = {"approve", "conditional-approve", "decline", "hold"}
UNAPPROVED_TYPES = {"market", "research"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    deal = doc.get("deal") or {}
    for k in REQUIRED_DEAL:
        if not deal.get(k):
            errors.append(f"deal: missing '{k}'")
    if deal.get("recommended_action") and deal["recommended_action"] not in RECOMMENDATIONS:
        warnings.append(f"deal.recommended_action {deal['recommended_action']!r} is non-standard "
                        f"(expected one of {sorted(RECOMMENDATIONS)}) -> treat as a proposal, not a decision")

    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        return errors, warnings
    src_ids = set()
    for i, s in enumerate(sources):
        sid = s.get("source_id")
        if not sid:
            errors.append(f"sources[{i}]: missing 'source_id'")
        if sid in src_ids:
            errors.append(f"sources[{i}]: duplicate source_id {sid!r}")
        src_ids.add(sid)
        if s.get("type") in UNAPPROVED_TYPES and not s.get("approved"):
            warnings.append(f"source {sid!r} ({s.get('type')}) is not marked approved -> "
                            f"claims relying on it will be blocked as unapproved (needs-data)")

    model = doc.get("model") or {}
    entry = model.get("entry") or {}
    lev = model.get("leverage") or {}
    ret = model.get("returns") or {}
    for path, obj, keys in (("model.entry", entry, ("ev", "metric_value", "net_debt", "entry_multiple")),
                            ("model.leverage", lev, ("total_debt", "ebitda", "leverage_x")),
                            ("model.returns", ret, ("moic", "irr", "hold_years"))):
        for k in keys:
            if obj.get(k) is None:
                errors.append(f"{path}: missing '{k}'")
    if not model.get("source_id"):
        errors.append("model: missing 'source_id'")

    scenarios = doc.get("scenarios") or []
    if not scenarios:
        errors.append("scenarios must be a non-empty list")
    names = {str(s.get("name", "")).strip().lower() for s in scenarios}
    if "downside" not in names:
        warnings.append("no Downside scenario supplied -> return/downside completeness will fail (needs-data)")
    if "base" not in names:
        warnings.append("no Base scenario supplied -> cannot tie the memo to the model (needs-data)")

    # every claim-bearing item must carry a source_id (referential completeness)
    def _needs_src(label, items, field):
        for j, it in enumerate(items or []):
            sid = it.get("source_id")
            if not sid:
                warnings.append(f"{label}[{j}] has no source_id -> claim will be flagged unsupported")
            elif sid not in src_ids:
                warnings.append(f"{label}[{j}] cites source {sid!r} not in sources[] -> unsupported")

    _needs_src("thesis_points", doc.get("thesis_points"), "claim")
    _needs_src("risks", doc.get("risks"), "risk")
    _needs_src("scenarios", scenarios, "name")
    if (doc.get("valuation") or {}).get("source_id") not in src_ids:
        warnings.append("valuation.source_id not in sources[] -> unsupported")
    if (doc.get("sizing") or {}).get("source_id") not in src_ids:
        warnings.append("sizing.source_id not in sources[] -> unsupported")

    sizing = doc.get("sizing") or {}
    if not sizing.get("fund_nav"):
        errors.append("sizing: missing 'fund_nav' (needed to compute position size)")
    if sizing.get("proposed_commitment") is None:
        errors.append("sizing: missing 'proposed_commitment'")
    if sizing.get("single_name_limit_pct") is None:
        warnings.append("sizing: no single_name_limit_pct -> concentration check cannot run")

    recorded = {a.get("role") for a in (doc.get("approvals") or []) if a.get("status") == "recorded"}
    for role in ("preparer", "reviewer"):
        if role not in recorded:
            warnings.append(f"approval '{role}' not yet recorded -> memo cannot be circulated until recorded")

    if not doc.get("decision_questions"):
        warnings.append("no decision_questions supplied -> committee has nothing to vote on (needs-data)")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ic_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
