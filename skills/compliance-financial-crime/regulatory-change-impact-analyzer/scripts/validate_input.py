#!/usr/bin/env python3
"""Deterministic input validation for regulatory-change-impact-analyzer.

Validates a regulatory-change assessment file before impact analysis. Fails closed on
structural problems; warns on data-quality gaps that limit which findings are evaluable or
that will surface as findings downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  change_id, as_of (YYYY-MM-DD), config_version,
  instrument{authority, citation, authority_level, jurisdiction, publication_date,
             effective_date, source_ref},
  obligations[{obligation_id, text, obligation_type, applies_to_lines[], conflicts_with[],
               source_ref}],
  firm_profile{business_lines[], jurisdictions[]},
  inventory{mappings[{obligation_id, policies[], controls[], systems[], data_elements[],
             training[], owner{role}}]},
  config{...thresholds...}

Usage:
  python validate_input.py change.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("change_id", "as_of", "config_version", "instrument", "obligations", "firm_profile")
REQUIRED_INSTRUMENT = ("authority", "citation", "authority_level", "jurisdiction",
                       "effective_date", "source_ref")
REQUIRED_OBLIGATION = ("obligation_id", "text", "obligation_type", "source_ref")
ALLOWED_LEVELS = {"law", "regulation", "supervisory_guidance", "standard", "rule"}


def _date_ok(v) -> bool:
    if not DATE_RE.match(str(v)):
        return False
    try:
        datetime.strptime(str(v), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _date_ok(doc["as_of"]):
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")

    inst = doc.get("instrument") or {}
    if not isinstance(inst, dict):
        errors.append("instrument must be an object")
        return errors, warnings
    for k in REQUIRED_INSTRUMENT:
        if not inst.get(k):
            errors.append(f"instrument missing '{k}'")
    if inst.get("effective_date") and not _date_ok(inst["effective_date"]):
        errors.append(f"instrument.effective_date must be YYYY-MM-DD, got {inst.get('effective_date')!r}")
    if inst.get("publication_date") and not _date_ok(inst["publication_date"]):
        errors.append(f"instrument.publication_date must be YYYY-MM-DD, got {inst.get('publication_date')!r}")
    if inst.get("authority_level") and inst["authority_level"] not in ALLOWED_LEVELS:
        warnings.append(f"instrument.authority_level {inst.get('authority_level')!r} not in {sorted(ALLOWED_LEVELS)}")
    if not inst.get("publication_date"):
        warnings.append("instrument has no publication_date — retroactive-effective check cannot run")

    obls = doc.get("obligations")
    if not isinstance(obls, list) or not obls:
        errors.append("obligations must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, o in enumerate(obls):
        tag = f"obligations[{i}] ({o.get('obligation_id', '?')})"
        for k in REQUIRED_OBLIGATION:
            if not o.get(k):
                errors.append(f"{tag}: missing '{k}'")
        oid = o.get("obligation_id")
        if oid in ids:
            errors.append(f"{tag}: duplicate obligation_id")
        ids.add(oid)
        if not o.get("applies_to_lines"):
            warnings.append(f"{tag}: no applies_to_lines — treated as firm-wide; confirm scope")

    firm = doc.get("firm_profile") or {}
    if not firm.get("jurisdictions"):
        errors.append("firm_profile.jurisdictions must be a non-empty list (applicability needs it)")
    if not firm.get("business_lines"):
        warnings.append("firm_profile.business_lines empty — only firm-wide obligations will map to a line")

    mappings = (doc.get("inventory") or {}).get("mappings", [])
    mapped_ids = {m.get("obligation_id") for m in mappings}
    for oid in ids:
        if oid not in mapped_ids:
            warnings.append(f"obligation {oid} has no inventory mapping — mapping_gap/owner_gap will flag it if applicable")
    for m in mappings:
        if m.get("obligation_id") not in ids:
            warnings.append(f"inventory mapping references unknown obligation_id {m.get('obligation_id')!r}")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "change_example.json"
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
