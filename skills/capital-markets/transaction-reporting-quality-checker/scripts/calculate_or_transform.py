#!/usr/bin/env python3
"""Deterministic transaction-reporting quality-control engine.

Reads a reporting-batch file (see validate_input.py), reconciles submitted regulatory
transaction reports against the front-office source of record, and produces an
exception pack: completeness gaps, timeliness breaches, identifier-format defects,
missing mandatory fields, field-mapping/economic mismatches, and unresolved rejects.
Each exception carries cited evidence. The exception set maps deterministically to a
suggested remediation-priority band (see references/domain-rules.md).

IMPORTANT: This produces quality-control *findings and a triage suggestion* only. It
never makes a compliance determination ("in breach"), never decides a transaction is
not reportable, and never submits, amends, cancels, or suppresses a report. Those are
human/authorized-system actions.

Usage:
  python calculate_or_transform.py batch.json | --selftest
Prints the quality-control pack JSON to stdout.
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Quality-control findings only; not a compliance determination. No regulatory "
              "report has been submitted, amended, cancelled, or suppressed.")

DEFAULT_CONFIG = {
    "timeliness_deadline_hours": 24,
    "required_fields": ["reporting_firm_lei", "buyer_id", "seller_id", "instrument_isin",
                        "trading_venue_mic", "price", "quantity", "trade_datetime", "transaction_ref"],
    "identifier_fields": {"reporting_firm_lei": "lei", "buyer_id": "lei", "seller_id": "lei",
                          "instrument_isin": "isin", "trading_venue_mic": "mic"},
    "identifier_formats": {"lei": r"^[A-Z0-9]{18}[0-9]{2}$", "isin": r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",
                           "mic": r"^[A-Z0-9]{4}$"},
    "economic_fields": ["instrument_isin", "price", "quantity"],
    "price_tolerance_abs": 0.005,
    "supplementary_fields": ["trading_venue_mic"],
    "unresolved_statuses": ["rejected", "pending", "failed"],
}

# Canonical severity per exception code. Priority is derived from these, NOT from any
# severity a caller might place in the pack (defends the mapping against tampering).
SEVERITY_BY_CODE = {
    "missing_report": "blocking",
    "over_report": "blocking",
    "economic_field_mismatch": "blocking",
    "invalid_identifier": "high",
    "missing_required_field": "high",
    "late_report": "high",
    "rejected_report_unresolved": "high",
    "noncritical_field_mismatch": "low",
}


def _parse_dt(s: str):
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cite_exec(e: dict) -> str:
    return f"oms:{e.get('source_ref', '?')}@{e.get('execution_ts', '?')}"


def _cite_report(r: dict) -> str:
    return f"arm:{r.get('source_ref', '?')}@{r.get('report_submitted_ts', '?')}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    execs = doc.get("source_executions") or []
    reports = doc.get("submitted_reports") or []

    exec_by_ref = {e["transaction_ref"]: e for e in execs}
    report_by_ref = {r["transaction_ref"]: r for r in reports}
    reportable_refs = {e["transaction_ref"] for e in execs if e.get("reportable") is True}

    exceptions, not_evaluable = [], []

    def add(code, reason, evidence, detail=None):
        exceptions.append({
            "code": code,
            "severity": SEVERITY_BY_CODE.get(code, "high"),
            "reason": reason,
            "evidence": evidence,
            "detail": detail or {},
        })

    # ---- Completeness: reportable source execution with no submitted report ----
    for ref in sorted(reportable_refs):
        if ref not in report_by_ref:
            e = exec_by_ref[ref]
            add("missing_report",
                f"reportable execution {ref} has no matching submitted report",
                [{"transaction_ref": ref, "exec_id": e.get("exec_id"), "citation": _cite_exec(e)}])

    # ---- Over-reporting: submitted report with no matching reportable source ----
    for ref in sorted(report_by_ref):
        if ref not in reportable_refs:
            r = report_by_ref[ref]
            why = ("no source execution for this transaction_ref"
                   if ref not in exec_by_ref else "matching source execution is marked not reportable")
            add("over_report",
                f"submitted report {r.get('report_id')} for {ref} has no reportable source ({why})",
                [{"transaction_ref": ref, "report_id": r.get("report_id"), "citation": _cite_report(r)}])

    # ---- Per matched pair (reportable source AND a report) ----
    id_formats = {k: re.compile(v) for k, v in cfg["identifier_formats"].items()}
    deadline_h = float(cfg["timeliness_deadline_hours"])
    price_tol = float(cfg["price_tolerance_abs"])
    unresolved = {str(s).lower() for s in cfg["unresolved_statuses"]}

    for ref in sorted(reportable_refs & set(report_by_ref)):
        e = exec_by_ref[ref]
        r = report_by_ref[ref]
        rcite = _cite_report(r)

        # Timeliness
        et, rt = _parse_dt(e.get("execution_ts")), _parse_dt(r.get("report_submitted_ts"))
        if et and rt:
            lag_h = (rt - et).total_seconds() / 3600.0
            if lag_h > deadline_h:
                add("late_report",
                    f"report {r.get('report_id')} submitted {lag_h:.1f}h after execution, exceeds {deadline_h:.0f}h deadline",
                    [{"transaction_ref": ref, "report_id": r.get("report_id"), "citation": rcite}],
                    {"lag_hours": round(lag_h, 2), "deadline_hours": deadline_h})
        else:
            not_evaluable.append({"check": "late_report", "transaction_ref": ref, "why": "unparseable timestamp"})

        # Missing mandatory fields
        missing = [f for f in cfg["required_fields"] if r.get(f) in (None, "")]
        if missing:
            add("missing_required_field",
                f"report {r.get('report_id')} is missing mandatory field(s): {', '.join(missing)}",
                [{"transaction_ref": ref, "report_id": r.get("report_id"), "fields": missing, "citation": rcite}])

        # Identifier format
        for field, kind in cfg["identifier_fields"].items():
            val = r.get(field)
            if val in (None, ""):
                continue  # emptiness handled by missing_required_field
            rx = id_formats.get(kind)
            if rx and not rx.match(str(val)):
                add("invalid_identifier",
                    f"report {r.get('report_id')} field {field} value does not match required {kind.upper()} format",
                    [{"transaction_ref": ref, "report_id": r.get("report_id"), "field": field,
                      "value": str(val), "citation": rcite}])

        # Economic reconciliation (report value vs source of record)
        for field in cfg["economic_fields"]:
            sv, rv = e.get(field), r.get(field)
            if sv is None or rv is None:
                not_evaluable.append({"check": "economic_field_mismatch", "transaction_ref": ref,
                                      "field": field, "why": "value absent on source or report"})
                continue
            sn, rn = _num(sv), _num(rv)
            differs = (abs(sn - rn) > price_tol) if (sn is not None and rn is not None) else (str(sv) != str(rv))
            if differs:
                add("economic_field_mismatch",
                    f"report {r.get('report_id')} {field}={rv} differs from source {field}={sv}",
                    [{"transaction_ref": ref, "field": field, "reported": rv, "source": sv,
                      "citation_report": rcite, "citation_source": _cite_exec(e)}])

        # Supplementary (non-economic) reconciliation — low severity
        for field in cfg.get("supplementary_fields", []):
            sv, rv = e.get(field), r.get(field)
            if sv in (None, "") or rv in (None, ""):
                continue
            if str(sv) != str(rv):
                add("noncritical_field_mismatch",
                    f"report {r.get('report_id')} supplementary field {field}={rv} differs from source {sv}",
                    [{"transaction_ref": ref, "field": field, "reported": rv, "source": sv, "citation": rcite}])

        # Unresolved rejection
        if str(r.get("status", "")).lower() in unresolved:
            add("rejected_report_unresolved",
                f"report {r.get('report_id')} status is '{r.get('status')}' and is not yet resolved",
                [{"transaction_ref": ref, "report_id": r.get("report_id"),
                  "status": r.get("status"), "citation": rcite}])

    # ---- Deterministic remediation-priority mapping (see references/domain-rules.md) ----
    severities = {ex["severity"] for ex in exceptions}
    if "blocking" in severities:
        priority = "Blocking"
    elif "high" in severities:
        priority = "High"
    elif exceptions:
        priority = "Review"
    else:
        priority = "Clean"

    false_positive_checks = []
    if exceptions:
        false_positive_checks = [
            "confirm no reporting exemption, waiver, or deferral applies to the flagged transaction",
            "normalize timezones and cut-off calendars before treating a report as late",
            "confirm a correction is not already in flight before treating a reject as unresolved",
            "confirm the source-of-record field is itself correct before treating a mismatch as a report defect",
            "confirm the reference-data (LEI/ISIN/MIC) snapshot used is the effective one",
        ]

    return {
        "qc_id": f"trqc-{doc.get('report_regime', 'NA')}-{doc.get('as_of', 'NA')}-0001",
        "report_regime": doc.get("report_regime"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "population": {
            "source_reportable": len(reportable_refs),
            "submitted": len(report_by_ref),
            "matched": len(reportable_refs & set(report_by_ref)),
        },
        "exceptions": exceptions,
        "exception_codes": sorted({ex["code"] for ex in exceptions}),
        "not_evaluable": not_evaluable,
        "suggested_priority": priority,
        "false_positive_checks": false_positive_checks,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "reporting_batch_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
