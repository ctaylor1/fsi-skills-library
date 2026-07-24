#!/usr/bin/env python3
"""Deterministic payment-log diagnostics for payment-api-log-diagnostic-pack.

Redacts PAN, classifies each entry against the taxonomy, aggregates by category and endpoint,
picks the top failing endpoint and the most-frequent suspected cause, and maps categories to
suggested human-run checks. Evidence only; never remediates.

Usage: python calculate_or_transform.py logs.json | --selftest
"""
from __future__ import annotations
import json, re, sys
from collections import defaultdict
from pathlib import Path

DISCLAIMER = ("Diagnostic evidence only; no configuration has been changed, no key rotated, and "
              "no fix deployed. Cardholder data is redacted.")
PAN_RE = re.compile(r"\b\d{13,19}\b")


def redact(text) -> str:
    return PAN_RE.sub("[REDACTED-PAN]", str(text)) if text is not None else ""


def compute(doc: dict) -> dict:
    integ = doc["integration"]
    tax = doc["taxonomy"]
    code_map = {str(k): v for k, v in (tax.get("code_map") or {}).items()}
    next_map = tax.get("next_checks") or {}
    entries = doc["log_entries"]

    by_cat = defaultdict(int)
    by_endpoint = defaultdict(int)
    classified = []
    for e in entries:
        code = str(e.get("error_code"))
        cat = code_map.get(code, "unclassified")
        by_cat[cat] += 1
        by_endpoint[str(e.get("endpoint"))] += 1
        classified.append({
            "request_id": e.get("request_id"),
            "endpoint": e.get("endpoint"),
            "http_status": e.get("http_status"),
            "error_code": code,
            "category": cat,
            "message": redact(e.get("message")),  # PAN-redacted
        })

    top_endpoint = min(sorted(by_endpoint), key=lambda k: (-by_endpoint[k], k)) if by_endpoint else None
    suspected = min(sorted(by_cat), key=lambda k: (-by_cat[k], k)) if by_cat else None
    next_checks = next_map.get(suspected, []) if suspected else []

    return {
        "diagnostic_id": f"pald-{integ.get('integration_id', 'UNKNOWN')}-0001",
        "integration_id": integ.get("integration_id"),
        "gateway": integ.get("gateway"),
        "taxonomy_version": tax.get("config_version"),
        "total_failures": len(entries),
        "by_category": dict(sorted(by_cat.items())),
        "by_endpoint": dict(sorted(by_endpoint.items())),
        "top_endpoint": top_endpoint,
        "suspected_cause": suspected,
        "next_checks": next_checks,
        "classified_entries": classified,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "logs_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
