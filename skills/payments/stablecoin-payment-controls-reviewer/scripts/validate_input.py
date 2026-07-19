#!/usr/bin/env python3
"""Deterministic input validation for stablecoin-payment-controls-reviewer.

Validates a control-review file before the control rules run. Fails closed on structural
problems; warns on data-quality gaps that limit which controls are evaluable or that leave
a critical control unattested.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  program, as_of (YYYY-MM-DD), config_version, jurisdiction, config{...thresholds...},
  controls[{id, category, attested(bool, optional), metrics{...}, source_ref}]

Usage:
  python validate_input.py review.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("program", "as_of", "config_version", "controls")
REQUIRED_CTRL = ("id", "category", "source_ref")
CATEGORIES = {"reserve", "custody", "screening", "transaction",
              "operational", "reconciliation", "disclosure"}
KNOWN_CONTROLS = {
    "reserve_backing_ratio", "reserve_asset_quality", "reserve_attestation_current",
    "reserve_segregation", "custody_qualified_custodian", "key_management",
    "sanctions_wallet_screening", "travel_rule", "kyc_program", "txn_limits",
    "finality_confirmations", "address_allowlist", "incident_response", "reorg_handling",
    "onchain_ledger_recon", "mint_burn_recon", "redemption_disclosure", "reserve_reporting",
}
CRITICAL = {
    "reserve_backing_ratio", "reserve_asset_quality", "reserve_attestation_current",
    "custody_qualified_custodian", "sanctions_wallet_screening", "travel_rule",
    "onchain_ledger_recon",
}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    controls = doc.get("controls")
    if not isinstance(controls, list) or not controls:
        errors.append("controls must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, c in enumerate(controls):
        tag = f"controls[{i}] ({c.get('id', '?')})"
        for k in REQUIRED_CTRL:
            if k not in c or c[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        cat = c.get("category")
        if cat is not None and cat not in CATEGORIES:
            errors.append(f"{tag}: category {cat!r} not in {sorted(CATEGORIES)}")
        cid = c.get("id")
        if cid in ids:
            errors.append(f"{tag}: duplicate control id")
        ids.add(cid)
        if cid not in KNOWN_CONTROLS:
            warnings.append(f"{tag}: unknown control id — will be reported not_evaluable")
        if "metrics" in c and not isinstance(c["metrics"], dict):
            errors.append(f"{tag}: 'metrics' must be an object")
        if c.get("attested") is False and cid in CRITICAL:
            warnings.append(f"{tag}: critical control attested as not implemented — expect escalation")

    missing_critical = CRITICAL - ids
    if missing_critical:
        warnings.append(
            "critical control(s) not present in review — coverage incomplete: "
            + ", ".join(sorted(missing_critical)))
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "review_example.json"
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
