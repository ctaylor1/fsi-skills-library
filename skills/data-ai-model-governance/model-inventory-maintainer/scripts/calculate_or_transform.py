#!/usr/bin/env python3
"""Deterministic inventory-change computation for model-inventory-maintainer.

Reads an inventory change request (see validate_input.py) and derives a PROPOSED inventory
change proposal:
  - completeness vs the required attribute set,
  - the materiality tier from the documented factors (versioned rubric),
  - lifecycle-transition validity,
  - source reconciliation with a typed break taxonomy,
  - findings, each with cited evidence.

IMPORTANT: This produces a PROPOSED proposal for human adjudication only. It never posts to
the inventory, approves/attests a model, or closes a finding. The materiality mapping and
lifecycle map are deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py request.json | --selftest
Prints the proposal JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

REQUIRED_ATTRS = ("name", "owner", "purpose", "lifecycle_status", "materiality_factors",
                  "versions", "dependencies", "lineage", "approvals")
FACTOR_KEYS = ("financial_exposure", "decision_autonomy", "customer_impact", "regulatory_use")
RECONCILE_ATTRS = ("name", "owner", "lifecycle_status", "latest_version")

DEFAULT_CONFIG = {
    "tier1_min": 8, "tier2_min": 4, "escalate_at": 3,
    "escalating_factors": ["decision_autonomy", "regulatory_use"],
    "staleness_days": 90,
}
ALLOWED_TRANSITIONS = {
    "proposed": {"in-development", "retired"},
    "in-development": {"in-validation", "on-hold", "retired"},
    "in-validation": {"approved", "in-development", "on-hold", "retired"},
    "approved": {"in-use", "in-validation", "retired"},
    "in-use": {"in-validation", "on-hold", "retired"},
    "on-hold": {"in-development", "in-validation", "in-use", "retired"},
    "retired": set(),
}
DISCLAIMER = ("Proposed inventory changes and findings only; not an approval, attestation, "
              "or system-of-record update. Model Risk Governance adjudication is required "
              "before any change is posted.")


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def materiality_tier(factors: dict, cfg: dict) -> tuple[str, int]:
    score = sum(int(factors.get(k, 0) or 0) for k in FACTOR_KEYS)
    escalate = any(int(factors.get(k, 0) or 0) >= cfg["escalate_at"]
                   for k in cfg["escalating_factors"])
    if score >= cfg["tier1_min"] or escalate:
        return "Tier 1", score
    if score >= cfg["tier2_min"]:
        return "Tier 2", score
    return "Tier 3", score


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    rec = doc["proposed_record"]
    cur = doc.get("current_record") or {}
    sources = doc.get("sources") or {}
    registry = sources.get("registry") or {}
    evidence = doc.get("evidence") or []
    as_of = _parse_date(doc["as_of"])

    # index evidence by attribute for citation attachment
    ev_by_attr: dict[str, list] = {}
    for e in evidence:
        ev_by_attr.setdefault(e.get("attribute"), []).append(
            {"system": e.get("system"), "citation": e.get("source_ref")})

    findings = []

    def add_finding(fid, attribute, severity, description, ev_rows):
        findings.append({"id": fid, "attribute": attribute, "severity": severity,
                         "description": description, "evidence": ev_rows})

    # --- completeness -------------------------------------------------------
    present, missing = [], []
    for a in REQUIRED_ATTRS:
        if a in rec and rec[a] not in (None, "", [], {}):
            present.append(a)
        else:
            missing.append(a)
            add_finding(f"F-COMPLETE-{a}", a, "medium",
                        f"required attribute '{a}' is missing or empty",
                        [{"system": "rubric",
                          "citation": f"rubric:{doc['config_version']}#required-attributes"}])

    # --- materiality tie-out ------------------------------------------------
    factors = rec.get("materiality_factors") or {}
    computed_tier, score = materiality_tier(factors, cfg)
    proposed_tier = rec.get("materiality_tier")
    tie_out = {"factors": {k: int(factors.get(k, 0) or 0) for k in FACTOR_KEYS},
               "score": score, "computed_tier": computed_tier,
               "proposed_tier": proposed_tier,
               "rubric": f"{doc['config_version']}",
               # Echo the EFFECTIVE tier thresholds this compute step used (defaults merged
               # with the doc's config override) so validate_output re-derives the tier with
               # the same rubric config, not the hardcoded default.
               "config": {"tier1_min": int(cfg["tier1_min"]),
                          "tier2_min": int(cfg["tier2_min"]),
                          "escalate_at": int(cfg["escalate_at"]),
                          "escalating_factors": list(cfg["escalating_factors"])}}
    if proposed_tier is not None and proposed_tier != computed_tier:
        add_finding("F-MATERIALITY", "materiality_tier", "high",
                    f"proposed materiality tier {proposed_tier!r} does not match rubric-computed "
                    f"{computed_tier!r} (score {score})",
                    ev_by_attr.get("materiality_factors")
                    or [{"system": "rubric", "citation": f"rubric:{doc['config_version']}#materiality"}])

    # --- lifecycle transition ----------------------------------------------
    to_state = rec.get("lifecycle_status")
    from_state = cur.get("lifecycle_status") if doc["change_type"] == "update" else None
    lifecycle = {"from": from_state, "to": to_state, "valid_transition": True, "reason": ""}
    if doc["change_type"] == "update" and from_state is not None and to_state is not None:
        allowed = ALLOWED_TRANSITIONS.get(from_state, set())
        if from_state == to_state:
            lifecycle["reason"] = "no lifecycle change"
        elif to_state not in allowed:
            lifecycle["valid_transition"] = False
            lifecycle["reason"] = f"{from_state} -> {to_state} not in allowed transitions"
            add_finding("F-LIFECYCLE", "lifecycle_status", "high",
                        f"invalid lifecycle transition {from_state} -> {to_state}",
                        ev_by_attr.get("lifecycle_status")
                        or [{"system": "policy", "citation": f"rubric:{doc['config_version']}#lifecycle"}])
        else:
            lifecycle["reason"] = f"{from_state} -> {to_state} permitted"
    elif doc["change_type"] == "create":
        lifecycle["reason"] = "create — no prior state"
        if to_state in ("approved", "in-use") and not (rec.get("approvals")):
            add_finding("F-LIFECYCLE-CREATE", "lifecycle_status", "high",
                        f"create declares '{to_state}' without approvals evidence",
                        [{"system": "rubric", "citation": f"rubric:{doc['config_version']}#lifecycle"}])

    # --- source reconciliation ---------------------------------------------
    reconciliation = []
    snap_date = _parse_date(registry.get("snapshot_date")) if registry else None
    stale = bool(snap_date and as_of and (as_of - snap_date).days > cfg["staleness_days"])
    for a in RECONCILE_ATTRS:
        inv_v = rec.get(a)
        src_v = registry.get(a) if registry else None
        row = {"attribute": a, "inventory_value": inv_v, "source_value": src_v,
               "system": "registry"}
        if not registry or (a not in registry and inv_v is not None):
            row["result"] = "unverifiable" if not registry else "break"
            if registry:
                row["break_type"] = "missing_in_source"
        elif inv_v is None and src_v is not None:
            row["result"] = "break"; row["break_type"] = "missing_in_inventory"
        elif inv_v is not None and src_v is None:
            row["result"] = "break"; row["break_type"] = "missing_in_source"
        elif str(inv_v) == str(src_v):
            row["result"] = "stale" if stale else "match"
            if stale:
                row["break_type"] = "stale"
        else:
            row["result"] = "break"; row["break_type"] = "value_mismatch"
        reconciliation.append(row)
        if row.get("break_type"):
            cite = [{"system": "registry",
                     "citation": registry.get("source_ref", f"registry:record={doc['record_id']}")},
                    {"system": "inventory",
                     "citation": f"proposal:record={doc['record_id']};attr={a}"}]
            add_finding(f"F-RECON-{a}", a, "medium" if row["break_type"] != "value_mismatch" else "high",
                        f"reconciliation break ({row['break_type']}) on '{a}': "
                        f"inventory={inv_v!r} vs registry={src_v!r}", cite)

    breaks = [r for r in reconciliation if r.get("break_type")]

    narrative = (
        f"Inventory {doc['change_type']} proposal for {doc['asset_kind']} record "
        f"{doc['record_id']} (as of {doc['as_of']}). Rubric-computed materiality: "
        f"{computed_tier} (score {score}). {len(present)}/{len(REQUIRED_ATTRS)} required "
        f"attributes present; {len(breaks)} reconciliation break(s); "
        f"{len(findings)} finding(s) recorded. This proposal requires adjudication by Model "
        f"Risk Governance before any change is posted. " + DISCLAIMER)

    return {
        "proposal_id": f"mim-{str(doc['record_id']).replace('*','')}-{doc['as_of']}-0001",
        "record_id": doc["record_id"],
        "as_of": doc["as_of"],
        "config_version": doc["config_version"],
        "change_type": doc["change_type"],
        "asset_kind": doc["asset_kind"],
        "status": "proposed",
        "computed_materiality_tier": computed_tier,
        "proposed_materiality_tier": proposed_tier,
        "materiality_tie_out": tie_out,
        "completeness": {"required": list(REQUIRED_ATTRS), "present": present, "missing": missing},
        "lifecycle": lifecycle,
        "reconciliation": reconciliation,
        "findings": findings,
        "requires_adjudication": True,
        "adjudication_owner": "Model Risk Governance",
        "narrative": narrative,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "change_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
