#!/usr/bin/env python3
"""Deterministic input validation for transaction-reporting-quality-checker.

Validates a reporting-batch file before quality-control checks run. Fails closed on
structural problems; warns on data-quality gaps that limit which checks are evaluable
(so the reviewer knows a clean run does not imply full coverage).

Input schema (JSON): see references/source-map.md. Key fields:
  report_regime, as_of (YYYY-MM-DD), config_version, config{...thresholds/formats...},
  source_executions[{exec_id,transaction_ref,execution_ts,price,quantity,
                     instrument_isin,reportable,source_ref}],
  submitted_reports[{report_id,transaction_ref,status,report_submitted_ts,source_ref,
                     ...reported field values...}]

Usage:
  python validate_input.py batch.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("report_regime", "as_of", "config_version", "source_executions", "submitted_reports")
REQUIRED_EXEC = ("exec_id", "transaction_ref", "execution_ts", "reportable", "source_ref")
REQUIRED_REPORT = ("report_id", "transaction_ref", "status", "report_submitted_ts", "source_ref")


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

    execs = doc.get("source_executions")
    reports = doc.get("submitted_reports")
    if not isinstance(execs, list):
        errors.append("source_executions must be a list")
        execs = []
    if not isinstance(reports, list):
        errors.append("submitted_reports must be a list")
        reports = []
    if not execs and not reports:
        errors.append("both source_executions and submitted_reports are empty — nothing to check")
        return errors, warnings

    exec_refs, timed_exec = set(), 0
    for i, e in enumerate(execs):
        tag = f"source_executions[{i}] ({e.get('exec_id','?')})"
        for k in REQUIRED_EXEC:
            if k not in e or e[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if not isinstance(e.get("reportable"), bool):
            errors.append(f"{tag}: 'reportable' must be boolean true/false")
        ref = e.get("transaction_ref")
        if ref in exec_refs:
            warnings.append(f"{tag}: duplicate transaction_ref {ref!r} in source (many-to-one match ambiguity)")
        exec_refs.add(ref)
        if "T" in str(e.get("execution_ts", "")):
            timed_exec += 1

    report_refs, timed_rpt = set(), 0
    for i, r in enumerate(reports):
        tag = f"submitted_reports[{i}] ({r.get('report_id','?')})"
        for k in REQUIRED_REPORT:
            if k not in r or r[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        ref = r.get("transaction_ref")
        if ref in report_refs:
            warnings.append(f"{tag}: duplicate transaction_ref {ref!r} in reports (possible double-report)")
        report_refs.add(ref)
        if "T" in str(r.get("report_submitted_ts", "")):
            timed_rpt += 1

    cfg = doc.get("config") or {}
    if not cfg:
        warnings.append("no 'config' block — default thresholds/formats will be used; record the config_version")
    if not cfg.get("required_fields"):
        warnings.append("config.required_fields absent — completeness-of-field check uses defaults")
    if not cfg.get("identifier_formats"):
        warnings.append("config.identifier_formats absent — identifier-format check uses defaults")
    if execs and timed_exec == 0:
        warnings.append("no source execution has a timestamp — timeliness (late_report) is not evaluable")
    if reports and timed_rpt == 0:
        warnings.append("no submitted report has a timestamp — timeliness (late_report) is not evaluable")
    if not (exec_refs & report_refs):
        warnings.append("no transaction_ref appears in both source and reports — reconciliation/timeliness checks will have nothing to match")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reporting_batch_example.json"
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
