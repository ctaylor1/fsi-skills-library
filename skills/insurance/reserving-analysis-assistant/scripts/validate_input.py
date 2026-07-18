#!/usr/bin/env python3
"""Deterministic input validation for reserving-analysis-assistant.

Validates a reserving dataset (loss-development triangles + optional counts/exposure/large
losses) before any reserve analysis is drafted. Fails closed on structural problems (so an
analysis is never assembled from an ill-formed dataset); warns on data gaps or triangle
patterns that will force a `needs-data` or `anomaly-flagged` disposition downstream.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  dataset_version, valuation_date, currency, unit, large_loss_threshold, segments[
    {segment_id, line_of_business, triangle_basis (paid|incurred), origin_label,
     triangle{origin: [cumulative amounts by development period]}, tail_factor?,
     factor_method? (volume-weighted|simple-average), claim_counts{origin:n}?,
     earned_exposure{origin:x}?, large_losses[{claim_id, origin, amount, source_ref}]?,
     large_loss_threshold?, source_ref}]

Usage: python validate_input.py triangles.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

REQUIRED_TOP = ("dataset_version", "valuation_date", "segments")
REQUIRED_SEGMENT = ("segment_id", "line_of_business", "triangle_basis", "triangle", "source_ref")
TRIANGLE_BASES = {"paid", "incurred"}
FACTOR_METHODS = {"volume-weighted", "simple-average"}


def _is_iso_date(v) -> bool:
    try:
        date.fromisoformat(str(v))
        return True
    except Exception:
        return False


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_iso_date(doc.get("valuation_date")):
        errors.append("valuation_date is not an ISO date (YYYY-MM-DD)")
    if "large_loss_threshold" in doc and not _is_number(doc.get("large_loss_threshold")):
        errors.append("large_loss_threshold must be numeric")

    segments = doc.get("segments") or []
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, s in enumerate(segments):
        tag = f"segments[{i}] ({s.get('segment_id', '?')})"
        for k in REQUIRED_SEGMENT:
            if k not in s or s[k] in (None, "", [], {}):
                errors.append(f"{tag}: missing '{k}'")
        sid = s.get("segment_id")
        if sid in ids:
            errors.append(f"{tag}: duplicate segment_id")
        ids.add(sid)

        basis = s.get("triangle_basis")
        if basis is not None and basis not in TRIANGLE_BASES:
            errors.append(f"{tag}: triangle_basis {basis!r} must be one of {sorted(TRIANGLE_BASES)}")
        method = s.get("factor_method")
        if method is not None and method not in FACTOR_METHODS:
            errors.append(f"{tag}: factor_method {method!r} must be one of {sorted(FACTOR_METHODS)}")
        if "tail_factor" in s and not _is_number(s.get("tail_factor")):
            errors.append(f"{tag}: tail_factor must be numeric")

        tri = s.get("triangle")
        if not isinstance(tri, dict) or not tri:
            errors.append(f"{tag}: triangle must be a non-empty object keyed by origin period")
            continue

        max_len = 0
        for origin, row in tri.items():
            if not isinstance(row, list) or not row:
                errors.append(f"{tag}: triangle['{origin}'] must be a non-empty list of cumulative amounts")
                continue
            if not all(_is_number(v) for v in row):
                errors.append(f"{tag}: triangle['{origin}'] contains a non-numeric value")
                continue
            max_len = max(max_len, len(row))
            # anomaly pre-warnings (do not error; the engine flags these for actuarial review)
            for j in range(len(row) - 1):
                a, b = row[j], row[j + 1]
                if a in (0, None):
                    warnings.append(f"{tag}: triangle['{origin}'] has a zero/None at dev {j + 1} -> factor undefined (needs-data/anomaly)")
                    continue
                if basis == "paid" and b < a:
                    warnings.append(f"{tag}: triangle['{origin}'] paid cumulative decreases dev {j + 1}->{j + 2} -> anomaly-flagged")
                elif basis == "incurred" and a and (b / a) < 0.80:
                    warnings.append(f"{tag}: triangle['{origin}'] incurred drops >20% dev {j + 1}->{j + 2} -> anomaly-flagged")

        if max_len < 2:
            warnings.append(f"{tag}: triangle has < 2 development periods -> no development factor computable (needs-data)")

        for optional in ("claim_counts", "earned_exposure"):
            if optional in s and not isinstance(s.get(optional), dict):
                errors.append(f"{tag}: {optional} must be an object keyed by origin period")

        for j, c in enumerate(s.get("large_losses") or []):
            if not c.get("claim_id") or not _is_number(c.get("amount")):
                errors.append(f"{tag}: large_losses[{j}] needs claim_id and a numeric amount")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "triangles_example.json"
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
