#!/usr/bin/env python3
"""Deterministic input validation for performance-attribution-builder.

Validates a performance-attribution intake bundle before the attribution is built. Fails closed
on structural problems (unknown model, missing period/ids, malformed segments/approvals); warns on
data gaps that will surface as open items (segments missing returns, weights that do not sum to
~1.0, a segment currency with no supplied currency return, no official returns to reconcile to).

Input schema (JSON): see references/source-map.md. Key fields:
  model, config_version, template_version, attribution_id, period{from,to}, portfolio_id,
  benchmark_id, base_currency, config{reconciliation_tolerance, weight_tolerance,
  official_tolerance}, official_returns{portfolio, benchmark}, required_approvals[],
  approvals[{type, approver_role, approver, status, date, source_ref}],
  segments[{segment, currency, weight_port, weight_bench, local_return_port, local_return_bench,
  currency_return, source_ref}]

Usage: python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("model", "attribution_id", "period", "portfolio_id", "benchmark_id",
                "base_currency", "segments")
REQUIRED_SEGMENT = ("segment", "currency", "weight_port", "weight_bench", "source_ref")
RETURN_FIELDS = ("local_return_port", "local_return_bench", "currency_return")
SUPPORTED_MODELS = {"brinson-fachler-arithmetic", "brinson-fachler", "arithmetic"}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if doc.get("model") not in SUPPORTED_MODELS:
        errors.append(f"unsupported attribution model {doc.get('model')!r}; this skill implements "
                      f"arithmetic Brinson-Fachler ({sorted(SUPPORTED_MODELS)})")

    per = doc.get("period") or {}
    if not (per.get("from") and per.get("to")):
        errors.append("period requires 'from' and 'to'")

    base = doc.get("base_currency")
    cfg = doc.get("config") or {}
    weight_tol = cfg.get("weight_tolerance", 0.005)

    segments = doc.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("segments must be a non-empty list")
        return errors, warnings

    names = set()
    sum_wp = sum_wb = 0.0
    for i, s in enumerate(segments):
        tag = f"segments[{i}] ({s.get('segment','?')})"
        for k in REQUIRED_SEGMENT:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        for k in ("weight_port", "weight_bench"):
            if k in s and not _num(s[k]):
                errors.append(f"{tag}: '{k}' must be numeric")
        nm = s.get("segment")
        if nm in names:
            errors.append(f"{tag}: duplicate segment name")
        names.add(nm)
        sum_wp += float(s.get("weight_port") or 0) if _num(s.get("weight_port")) else 0.0
        sum_wb += float(s.get("weight_bench") or 0) if _num(s.get("weight_bench")) else 0.0
        missing = [k for k in RETURN_FIELDS if not _num(s.get(k))]
        if missing:
            warnings.append(f"{tag}: missing return(s) {missing} -> segment becomes needs-data; "
                            "its weight is unattributed (open-item)")
        if base and s.get("currency") and s.get("currency") != base and s.get("currency_return") == 0:
            warnings.append(f"{tag}: non-base currency {s.get('currency')!r} with currency_return 0 "
                            "-> confirm hedged or supply the period currency return (open-item)")

    if abs(sum_wp - 1.0) > weight_tol:
        warnings.append(f"portfolio weights sum to {round(sum_wp, 6)} (expected ~1.0) -> "
                        "confirm cash/residual treatment (open-item)")
    if abs(sum_wb - 1.0) > weight_tol:
        warnings.append(f"benchmark weights sum to {round(sum_wb, 6)} (expected ~1.0) -> "
                        "confirm benchmark coverage (open-item)")

    off = doc.get("official_returns") or {}
    if not off or not (_num(off.get("portfolio")) or _num(off.get("benchmark"))):
        warnings.append("no official_returns supplied -> reconciliation to the book of record is "
                        "limited (open-item)")

    for i, a in enumerate(doc.get("approvals") or []):
        if not a.get("type") or not a.get("status"):
            errors.append(f"approvals[{i}]: requires 'type' and 'status'")
        if a.get("status") == "recorded" and not a.get("source_ref"):
            errors.append(f"approvals[{i}] ({a.get('type','?')}): recorded approval missing 'source_ref'")
    if not doc.get("required_approvals"):
        warnings.append("no required_approvals configured -> approval capture limited")
    if doc.get("approvals") is None:
        warnings.append("no approvals provided -> all required approvals will be outstanding")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "attribution_intake_example.json"
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
