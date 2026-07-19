#!/usr/bin/env python3
"""Deterministic input validation for suitability-reg-bi-reviewer.

Validates a recommendation packet before the Reg BI / FINRA 2111 obligation checks run.
Fails closed on structural problems; warns on data-quality gaps that limit which obligation
checks are evaluable (a warning surfaces as a gap or not-evaluable finding downstream, not a
silent pass).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  account_id, as_of (YYYY-MM-DD), config_version, customer_type ("retail"|"institutional"),
  recommendation{action, security{id,name,type,proprietary?}, amount?, account_type?},
  customer_profile{risk_tolerance,time_horizon_years,liquidity_needs,investment_objectives,
    financial_situation,investment_experience,...},
  disclosures[{type,delivered,date,source_ref}], costs{...}, alternatives_considered[...],
  conflicts[{type,description,disclosed,mitigation,source_ref}], supervision{...},
  product_due_diligence{...}, rollover_analysis{...}

Usage:
  python validate_input.py packet.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("account_id", "as_of", "config_version", "customer_type",
                "recommendation", "customer_profile")
ACTIONS = {"buy", "sell", "hold", "switch", "exchange", "rollover", "reallocate"}
CUSTOMER_TYPES = {"retail", "institutional"}
REQUIRED_PROFILE = ("risk_tolerance", "time_horizon_years", "liquidity_needs",
                    "investment_objectives", "financial_situation", "investment_experience")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if doc["customer_type"] not in CUSTOMER_TYPES:
        errors.append(f"customer_type must be one of {sorted(CUSTOMER_TYPES)}, got {doc['customer_type']!r}")

    rec = doc.get("recommendation")
    if not isinstance(rec, dict):
        errors.append("recommendation must be an object")
        return errors, warnings
    action = rec.get("action")
    if action not in ACTIONS:
        errors.append(f"recommendation.action must be one of {sorted(ACTIONS)}, got {action!r}")
    sec = rec.get("security")
    if not isinstance(sec, dict):
        errors.append("recommendation.security must be an object")
    else:
        for k in ("id", "name", "type"):
            if not sec.get(k):
                errors.append(f"recommendation.security missing '{k}'")

    prof = doc.get("customer_profile")
    if not isinstance(prof, dict) or not prof:
        # profile is required top-level; empty profile is a structural error (fail closed)
        errors.append("customer_profile must be a non-empty object")
    else:
        missing = [f for f in REQUIRED_PROFILE if prof.get(f) in (None, "", [], {})]
        if missing:
            warnings.append(f"customer_profile missing fields {missing} — care_profile_complete will be a gap")

    if errors:
        return errors, warnings

    # data-quality warnings (limit evaluability; surfaced as gaps / not-evaluable downstream)
    disclosures = doc.get("disclosures")
    if not disclosures:
        warnings.append("no 'disclosures' list — disclosure obligation checks are not evaluable (fail closed)")
    elif not isinstance(disclosures, list):
        errors.append("disclosures must be a list")
    if doc.get("costs") in (None, {}):
        warnings.append("no 'costs' block — care_cost_considered is not evaluable")
    if "alternatives_considered" not in doc:
        warnings.append("no 'alternatives_considered' — care_alternatives_considered will be a gap")
    if "conflicts" not in doc:
        warnings.append("no 'conflicts' inventory — conflict checks are not evaluable")
    if not doc.get("supervision"):
        warnings.append("no 'supervision' block — supervision_routed is not evaluable")
    if action == "rollover" and not doc.get("rollover_analysis"):
        warnings.append("rollover recommendation without 'rollover_analysis' — care_rollover_comparison will be a gap")
    if isinstance(sec, dict) and sec.get("proprietary") and not doc.get("conflicts"):
        warnings.append("proprietary security but no conflicts inventory — proprietary-conflict check not evaluable")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "recommendation_example.json"
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
