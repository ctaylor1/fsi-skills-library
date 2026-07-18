#!/usr/bin/env python3
"""Deterministic input validation for best-execution-reviewer.

Validates an executions file before best-execution checks run. Fails closed on structural
problems; warns on data-quality gaps that limit which checks are evaluable (missing
benchmark, missing timestamps, missing venue/cost).

Input schema (JSON): see references/source-map.md. Key fields:
  as_of (YYYY-MM-DD), policy_version, client_classification, config{...thresholds...},
  executions[{execution_id,order_id,symbol,instrument_class,side,order_type,order_qty,
    executed_qty,arrival_ts,execution_ts,execution_price,benchmark_price,benchmark_type,
    venue,commission,exception_flag,exception_rationale_ref,source_ref}]

Usage:
  python validate_input.py executions.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("as_of", "policy_version", "executions")
REQUIRED_EXE = ("execution_id", "order_id", "symbol", "side", "order_qty",
                "executed_qty", "execution_price", "source_ref")


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

    exes = doc.get("executions") or []
    if not isinstance(exes, list) or not exes:
        errors.append("executions must be a non-empty list")
        return errors, warnings

    cfg = doc.get("config") or {}
    approved = cfg.get("approved_venues") or []

    ids = set()
    priced = timed = venued = costed = 0
    for i, e in enumerate(exes):
        tag = f"executions[{i}] ({e.get('execution_id','?')})"
        for k in REQUIRED_EXE:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        for numk in ("order_qty", "executed_qty", "execution_price"):
            if _num(e.get(numk)) is None:
                errors.append(f"{tag}: {numk} not numeric")
        if e.get("side") not in ("buy", "sell"):
            errors.append(f"{tag}: side must be 'buy' or 'sell'")
        oq, xq = _num(e.get("order_qty")), _num(e.get("executed_qty"))
        if oq is not None and xq is not None and xq > oq:
            errors.append(f"{tag}: executed_qty {xq} exceeds order_qty {oq}")
        if oq == 0:
            errors.append(f"{tag}: order_qty must be > 0")
        eid = e.get("execution_id")
        if eid in ids:
            errors.append(f"{tag}: duplicate execution_id")
        ids.add(eid)

        if _num(e.get("benchmark_price")):
            priced += 1
        else:
            warnings.append(f"{tag}: no benchmark_price — price/cost checks not evaluable for this row")
        if e.get("arrival_ts") and e.get("execution_ts"):
            timed += 1
        else:
            warnings.append(f"{tag}: missing arrival_ts/execution_ts — latency not evaluable for this row")
        if e.get("venue"):
            venued += 1
        elif approved:
            warnings.append(f"{tag}: no venue but approved_venues configured — venue-policy check not evaluable for this row")
        if _num(e.get("commission")) is not None:
            costed += 1
        if e.get("exception_flag") and not str(e.get("exception_rationale_ref") or "").strip():
            warnings.append(f"{tag}: exception_flag set with no exception_rationale_ref — will fire exception_undocumented")

    if not approved:
        warnings.append("config.approved_venues empty — venue_off_policy is not enforced; supply the effective venue list")
    if priced == 0:
        warnings.append("no execution carries a benchmark_price — price and cost checks cannot run")
    if timed == 0:
        warnings.append("no execution carries both timestamps — slow_execution cannot run")
    if len(exes) < int(cfg.get("min_population", 5)):
        warnings.append(f"thin population ({len(exes)} executions) — findings are low-confidence for outlier checks")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the policy_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "executions_example.json"
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
