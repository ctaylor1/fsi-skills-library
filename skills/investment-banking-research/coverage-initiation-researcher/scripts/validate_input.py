#!/usr/bin/env python3
"""Deterministic input validation for coverage-initiation-researcher.

Validates a coverage-research dossier before assembly. Fails closed on structural problems;
warns on completeness/evaluability gaps that limit the draft (missing required sections,
uncited claims, thin forecast, false MNPI attestation).

Input schema (JSON): see references/source-map.md. Key fields:
  ticker, company_name, as_of (YYYY-MM-DD), analyst_id, config_version, currency,
  mnpi_attestation, sections[{section, claims[{text, citation}]}],
  forecast{years[], revenue[], ebit_margin[], citations[]},
  valuation{methods[{method, value_per_share, citation}], weights{}},
  proposed_rating{label}, approvals{supervisory_analyst, research_committee}, data_gaps[]

Usage:
  python validate_input.py dossier.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("ticker", "company_name", "as_of", "analyst_id", "config_version",
                "sections", "forecast", "valuation")
REQUIRED_SECTIONS = ("business_model", "industry", "competitive_position", "forecast",
                     "catalysts", "risks", "valuation", "thesis")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    # sections
    sections = doc.get("sections")
    if not isinstance(sections, list) or not sections:
        errors.append("sections must be a non-empty list")
    else:
        seen = set()
        for i, s in enumerate(sections):
            name = s.get("section")
            tag = f"sections[{i}] ({name or '?'})"
            if not name:
                errors.append(f"{tag}: missing 'section' name")
                continue
            if name in seen:
                errors.append(f"{tag}: duplicate section")
            seen.add(name)
            claims = s.get("claims") or []
            if not isinstance(claims, list) or not claims:
                warnings.append(f"{tag}: no claims — section will be unevidenced")
                continue
            for j, c in enumerate(claims):
                if not str(c.get("text") or "").strip():
                    errors.append(f"{tag}.claims[{j}]: missing 'text'")
                if not str(c.get("citation") or "").strip():
                    warnings.append(f"{tag}.claims[{j}]: missing citation — reduces evidence coverage")
        for req in REQUIRED_SECTIONS:
            if req not in seen:
                warnings.append(f"required section '{req}' absent — draft will be 'Not ready'")

    # forecast
    f = doc.get("forecast") or {}
    years, revenue = f.get("years") or [], f.get("revenue") or []
    if not years or not revenue:
        errors.append("forecast must include non-empty 'years' and 'revenue'")
    else:
        if len(years) != len(revenue):
            errors.append(f"forecast years ({len(years)}) and revenue ({len(revenue)}) length mismatch")
        if any(_num(r) is None for r in revenue):
            errors.append("forecast revenue values must be numeric")
        if not f.get("ebit_margin"):
            warnings.append("forecast has no 'ebit_margin' series — margin path unevidenced")
        if not f.get("citations"):
            warnings.append("forecast has no citations — forecast section may be unevidenced")

    # valuation
    v = doc.get("valuation") or {}
    methods = v.get("methods") or []
    if not isinstance(methods, list) or not methods:
        errors.append("valuation must include at least one method with a value_per_share")
    else:
        for i, m in enumerate(methods):
            if _num(m.get("value_per_share")) is None:
                errors.append(f"valuation.methods[{i}] ({m.get('method','?')}): value_per_share not numeric")
            if not str(m.get("citation") or "").strip():
                warnings.append(f"valuation.methods[{i}] ({m.get('method','?')}): missing citation")
        weights = v.get("weights") or {}
        if weights:
            wsum = sum(_num(w) or 0.0 for w in weights.values())
            if abs(wsum - 1.0) > 0.01:
                warnings.append(f"valuation weights sum {wsum:.4f} != 1.0 — blended midpoint will be omitted")
        else:
            warnings.append("valuation has no weights — blended midpoint will be omitted")

    if not doc.get("mnpi_attestation"):
        warnings.append("mnpi_attestation is not true — draft cannot proceed to delivery until attested")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "coverage_dossier_example.json"
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
