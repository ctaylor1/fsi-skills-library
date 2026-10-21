#!/usr/bin/env python3
"""Deterministic input validation for transaction-monitoring-scenario-evaluator.

Validates an investigation-run file before the typology engine evaluates it. Fails closed on
structural problems; warns on data-quality gaps that limit which typology rules are evaluable,
that disable freshness / deduplication, or that indicate a subject was not properly escalated
from first-line triage.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DD), config_version, max_staleness_days,
  open_cases[{fingerprint}],                       # previously-open cases, for dedup
  rules[{rule_id, type, ...typology thresholds...}],
  subjects[{subject_id, alert_id, escalated, escalation_source, risk_rating, data_as_of,
            profile{expected_period_txns,...}, accounts[], counterparties[],
            transactions[{txn_id,date,direction(in|out),amount,instrument,channel,
                          counterparty_id,counterparty_country}], prior_cases[]}]

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, math, re, sys
from pathlib import Path
from native_integrity import canonical_hash

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "subjects", "rules")
REQUIRED_SUBJECT = ("subject_id", "transactions")
REQUIRED_TXN = ("txn_id", "date", "direction", "amount")
RULE_TYPES = {"structuring", "pass_through", "geography", "velocity", "cash_intensity"}
DIRECTIONS = {"in", "out"}


def _num(v):
    try:
        if isinstance(v, bool):
            return None
        value = float(v)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _validate_impl(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if "max_staleness_days" not in doc:
        warnings.append("no 'max_staleness_days' — freshness is not evaluable this run; indicators may rest on stale data")
    if "open_cases" not in doc:
        warnings.append("no 'open_cases' baseline — deduplication is disabled; every indicator will be reported as new")

    rules = doc.get("rules") or []
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty list")
        return errors, warnings
    rids = set()
    for i, r in enumerate(rules):
        tag = f"rules[{i}] ({r.get('rule_id','?')})"
        if not r.get("rule_id"):
            errors.append(f"{tag}: missing rule_id")
        if r.get("rule_id") in rids:
            errors.append(f"{tag}: duplicate rule_id")
        rids.add(r.get("rule_id"))
        rtype = r.get("type")
        if rtype not in RULE_TYPES:
            errors.append(f"{tag}: type must be one of {sorted(RULE_TYPES)}, got {rtype!r}")
            continue
        if rtype == "structuring" and _num(r.get("threshold_amount")) is None:
            errors.append(f"{tag}: structuring rule needs numeric threshold_amount")
        if rtype == "pass_through" and _num(r.get("min_ratio_pct")) is None:
            errors.append(f"{tag}: pass_through rule needs numeric min_ratio_pct")
        if rtype == "geography":
            if _num(r.get("limit_pct")) is None:
                errors.append(f"{tag}: geography rule needs numeric limit_pct")
            if not r.get("high_risk_countries"):
                warnings.append(f"{tag}: geography rule has no high_risk_countries — nothing will fire")
        if rtype == "velocity" and _num(r.get("multiplier")) is None:
            errors.append(f"{tag}: velocity rule needs numeric multiplier")
        if rtype == "cash_intensity" and _num(r.get("limit_pct")) is None:
            errors.append(f"{tag}: cash_intensity rule needs numeric limit_pct")

    subjects = doc.get("subjects") or []
    if not isinstance(subjects, list) or not subjects:
        errors.append("subjects must be a non-empty list")
        return errors, warnings

    sids = set()
    for i, s in enumerate(subjects):
        tag = f"subjects[{i}] ({s.get('subject_id','?')})"
        for k in REQUIRED_SUBJECT:
            if k not in s or s[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        sid = s.get("subject_id")
        if sid in sids:
            errors.append(f"{tag}: duplicate subject_id")
        sids.add(sid)
        if not s.get("escalated"):
            warnings.append(f"{tag}: not marked escalated — this monitor investigates alerts escalated from first-line triage (aml-alert-triager)")
        if not s.get("alert_id"):
            warnings.append(f"{tag}: no alert_id — cannot tie the package back to the escalated alert")
        if not s.get("data_as_of"):
            warnings.append(f"{tag}: no data_as_of — freshness not evaluable for this subject")
        if not (s.get("profile") or {}).get("expected_period_txns"):
            warnings.append(f"{tag}: no profile.expected_period_txns — velocity rule not evaluable for this subject")
        txns = s.get("transactions") or []
        if not isinstance(txns, list) or not txns:
            errors.append(f"{tag}: transactions must be a non-empty list")
            continue
        seen_txn = set()
        has_cc = False
        for j, t in enumerate(txns):
            ttag = f"{tag}.transactions[{j}] ({t.get('txn_id','?')})"
            for k in REQUIRED_TXN:
                if k not in t or t[k] in (None, ""):
                    errors.append(f"{ttag}: missing '{k}'")
            if _num(t.get("amount")) is None:
                errors.append(f"{ttag}: amount not numeric")
            if str(t.get("direction")) not in DIRECTIONS:
                errors.append(f"{ttag}: direction must be one of {sorted(DIRECTIONS)}, got {t.get('direction')!r}")
            if t.get("date") and not DATE_RE.match(str(t.get("date"))):
                errors.append(f"{ttag}: date must start YYYY-MM-DD, got {t.get('date')!r}")
            tid = t.get("txn_id")
            if tid in seen_txn:
                warnings.append(f"{ttag}: repeated txn_id — chronology may double-count")
            seen_txn.add(tid)
            if t.get("counterparty_country"):
                has_cc = True
            if not t.get("instrument"):
                warnings.append(f"{ttag}: no instrument — structuring / cash-intensity not evaluable for this row")
        if not has_cc:
            warnings.append(f"{tag}: no counterparty_country on any transaction — geography rule not evaluable for this subject")

    return errors, warnings


INPUT_SHAPE = {
    "run_id": str, "as_of": str, "config_version": str,
    "rules": [{"rule_id": str, "type": str, "high_risk_countries": [str]}], "open_cases": [{}],
    "subjects": [{"subject_id": str, "profile": {}, "accounts": [{}], "counterparties": [{}], "prior_cases": [{}],
                  "observation_period": {"from": str, "to": str}, "baseline_period": {"from": str, "to": str},
                  "transactions": [{"txn_id": str, "date": str, "amount": (int, float), "direction": str}]}],
}

def _shape_errors(value, shape, path="$", optional=False):
    """Reject malformed supplied containers; absent evidence remains a domain gap."""
    if value is None and optional:
        return []
    if isinstance(shape, dict):
        if not isinstance(value, dict):
            return [f"{path} must be an object"]
        return [error for key, child in shape.items() if key in value
                for error in _shape_errors(value[key], child, f"{path}.{key}", optional=True)]
    if isinstance(shape, list):
        if not isinstance(value, list):
            return [f"{path} must be a list"]
        return [error for index, item in enumerate(value)
                for error in _shape_errors(item, shape[0], f"{path}[{index}]")]
    if not isinstance(value, shape) or (shape == (int, float) and isinstance(value, bool)):
        return [f"{path} has an invalid type"]
    return []


def validate(doc):
    """Validate the same intake boundary used by public calculators and native replay."""
    try:
        canonical_hash(doc)  # Reject non-finite and non-JSON values, including optional fields.
        errors = _shape_errors(doc, INPUT_SHAPE)
        if errors:
            return errors, []
        return _validate_impl(doc)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        return ["malformed input: " + str(exc)], []


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
