#!/usr/bin/env python3
"""Deterministic input validation for filing-disclosure-change-detector.

Validates a compare file (a prior filing and a current filing) before change detection.
Fails closed on structural problems (missing fields, duplicate section ids, a current
filing that predates the prior baseline); warns on data-quality gaps that limit which
change findings are evaluable (missing accession, missing exhibits, cross-form comparison).

Input schema (JSON): see references/source-map.md. Key fields:
  job_id?, issuer, as_of (YYYY-MM-DD), config_version?, config?{...},
  prior{form_type, period?, filing_date, accession?, sections[], exhibits?[]},
  current{... same shape ...}
  section: {section_id, title, text, kind?}
  exhibit: {exhibit_no, description?, hash?}

Usage:
  python validate_input.py compare.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("issuer", "as_of", "prior", "current")
REQUIRED_FILING = ("form_type", "filing_date", "sections")
REQUIRED_SECTION = ("section_id", "title", "text")


def _validate_filing(side: str, filing: dict, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(filing, dict):
        errors.append(f"{side} must be an object")
        return
    for k in REQUIRED_FILING:
        if k not in filing or filing[k] in (None, ""):
            errors.append(f"{side}: missing '{k}'")
    if "filing_date" in filing and not DATE_RE.match(str(filing["filing_date"])):
        errors.append(f"{side}.filing_date must start YYYY-MM-DD, got {filing['filing_date']!r}")
    if not filing.get("accession"):
        warnings.append(f"{side}: no 'accession' - citations will be less precise (no as-filed anchor)")

    sections = filing.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append(f"{side}.sections must be a non-empty list")
        return
    seen = set()
    for i, s in enumerate(sections):
        tag = f"{side}.sections[{i}] ({s.get('section_id', '?')})"
        for k in REQUIRED_SECTION:
            if k not in s or s[k] in (None, ""):
                if k == "text":
                    warnings.append(f"{tag}: empty 'text' - section not comparable for changed_language")
                else:
                    errors.append(f"{tag}: missing '{k}'")
        sid = str(s.get("section_id", ""))
        if sid in seen:
            errors.append(f"{tag}: duplicate section_id within {side}")
        seen.add(sid)

    exhibits = filing.get("exhibits")
    if exhibits is not None:
        if not isinstance(exhibits, list):
            errors.append(f"{side}.exhibits must be a list when present")
        else:
            ex_seen = set()
            for i, e in enumerate(exhibits):
                if not e.get("exhibit_no"):
                    errors.append(f"{side}.exhibits[{i}]: missing 'exhibit_no'")
                en = str(e.get("exhibit_no", ""))
                if en in ex_seen:
                    errors.append(f"{side}.exhibits[{i}]: duplicate exhibit_no {en!r}")
                ex_seen.add(en)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if not doc.get("config_version"):
        warnings.append("no 'config_version' - default detection config will be used; record the version")

    prior, current = doc["prior"], doc["current"]
    _validate_filing("prior", prior, errors, warnings)
    _validate_filing("current", current, errors, warnings)
    if errors:
        return errors, warnings

    # baseline ordering: the current filing must not predate the prior baseline
    pd, cd = str(prior.get("filing_date", "")), str(current.get("filing_date", ""))
    if DATE_RE.match(pd) and DATE_RE.match(cd) and cd[:10] < pd[:10]:
        errors.append(f"current.filing_date {cd[:10]} predates prior.filing_date {pd[:10]} "
                      "(current must be the later filing)")

    if prior.get("form_type") != current.get("form_type"):
        warnings.append(f"cross-form comparison ({prior.get('form_type')} vs {current.get('form_type')}) - "
                        "sections may not be like-for-like; confirm the comparison baseline")

    p_ids = {str(s.get("section_id")) for s in prior.get("sections", [])}
    c_ids = {str(s.get("section_id")) for s in current.get("sections", [])}
    if not (p_ids & c_ids):
        warnings.append("no overlapping section_id between filings - changed_language not evaluable; "
                        "confirm section_id alignment")
    if not (prior.get("exhibits") or current.get("exhibits")):
        warnings.append("no exhibits in either filing - exhibit change findings not evaluable")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "compare_example.json"
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
