#!/usr/bin/env python3
"""Reconcile supplied insurance datasets; never correct or certify source records."""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from insurance_contract import amount, build_artifact, stable_hash
from validate_input import validate

BASIS = ("definition_version", "currency", "unit", "financial_basis", "date_basis", "valuation_date")
DISCLAIMER = ("Data-lineage and break evidence only; no source data has been altered, no "
              "actuarial assumption selected, and no reserve data certified.")


def compute(doc):
    errors, warnings = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    current, prior_rows = doc["current"], doc.get("prior", [])
    cfg = doc.get("config", {})
    threshold = amount(cfg.get("movement_pct", 20)) / 100
    indexes = []
    breaks, comparisons, issues = [], [], list(warnings)

    def observation(row, side):
        return {"side": side, "source_ref": row["source_ref"], "value": str(amount(row["value"])),
                "basis": {field: row.get(field) for field in BASIS}}

    def brk(kind, row, detail, counterpart=None, observations=None):
        refs = [row.get("source_ref", "declared-expectation")]
        if counterpart:
            refs.append(counterpart.get("source_ref", "unknown"))
        if observations is not None:
            refs = list(dict.fromkeys(item["source_ref"] for item in observations))
        finding = {"type": kind, "key": row.get("key"), "metric": row.get("metric"),
                   "period": row.get("period"), "detail": detail, "source_refs": refs,
                   "citation": " | ".join(refs)}
        if observations is not None:
            finding["observations"] = observations
        breaks.append(finding)

    for side, rows in (("current", current), ("prior", prior_rows)):
        index = defaultdict(list)
        for row in rows:
            index[(row["key"], row["metric"], row["period"])].append(row)
        for records in index.values():
            if len(records) > 1:
                brk("duplicate" if side == "current" else "duplicate_prior", records[0],
                    f"{len(records)} {side} rows share key/metric/period; comparisons withheld",
                    observations=[observation(record, side) for record in records])
                issues.append(f"ambiguous {side} duplicate: {records[0]['key']}/{records[0]['metric']}/{records[0]['period']}")
        indexes.append(index)
    cur, prior = indexes
    expected = doc.get("expected_periods", [])
    series = {(row["key"], row["metric"]) for row in current + prior_rows}
    series.update((row["key"], row["metric"]) for row in doc.get("expected_series", []))
    for key, metric in sorted(series):
        for period in expected:
            if (key, metric, period) not in cur:
                brk("missing_period", {"key": key, "metric": metric, "period": period}, "expected current period is absent")
    for key in prior.keys() - cur.keys():
        brk("missing_current", prior[key][0], "prior row has no current counterpart; not treated as zero")

    baseline = cfg.get("definition_baseline_version")
    for key, rows in cur.items():
        row = rows[0]
        for record in rows:
            if baseline and record.get("definition_version") != baseline:
                brk("definition_shift", record, f"definition {record.get('definition_version')} differs from configured {baseline}")
        if key not in prior:
            if prior_rows:
                brk("new_series", row, "no matching prior observation; movement not evaluable")
            continue
        previous = prior[key][0]
        records = rows + prior[key]
        missing = [field for field in BASIS if any(not record.get(field) for record in records)]
        changed = [field for field in BASIS if any(record.get(field) != row.get(field) for record in records)]
        if missing or changed:
            brk("not_comparable", row, f"missing basis: {missing}; changed basis: {changed}", previous,
                observations=[observation(record, "current") for record in rows]
                + [observation(record, "prior") for record in prior[key]])
            issues.append(f"non-comparable observation: {'/'.join(key)}")
            continue
        if len(rows) != 1 or len(prior[key]) != 1:
            continue
        before, after = amount(previous["value"]), amount(row["value"])
        movement = None if before == 0 else (after - before) / abs(before)
        comparisons.append({"key": key[0], "metric": key[1], "period": key[2],
                            "prior": str(before), "current": str(after),
                            "absolute_change": str(after - before),
                            "movement_pct": None if movement is None else str(movement * 100),
                            "basis": {field: row[field] for field in BASIS},
                            "source_refs": [previous["source_ref"], row["source_ref"]]})
        if before == 0 and after != 0:
            brk("movement_from_zero", row, f"explicit zero baseline changed to {after}; percentage undefined", previous)
        elif movement is not None and abs(movement) > threshold and not row.get("documented_reason"):
            brk("unexplained_movement", row, f"movement {movement * 100}% exceeds threshold {threshold * 100}% without explanation", previous)
    coverage = {
        "duplicates": "evaluable", "missing_periods": "evaluable" if expected else "not_evaluable",
        "prior_reconciliation": "evaluable" if prior_rows else "not_evaluable",
        "movement": "evaluable" if comparisons and not any(b["type"] in {"duplicate", "duplicate_prior", "not_comparable", "new_series"} for b in breaks)
        else "partial" if comparisons else "not_evaluable",
        "definition_check": "evaluable" if all(r.get("definition_version") for r in current + prior_rows) else "not_evaluable",
    }
    partial = any(state != "evaluable" for state in coverage.values()) or bool(issues)
    disposition = "breaks-for-review" if breaks else "partial-not-evaluable" if partial else "clean"
    output = {"lineage_id": "idr-" + stable_hash(doc)[:16], "as_of": doc["as_of"], "config_version": doc.get("config_version"),
              "records_checked": len(current), "prior_records_checked": len(prior_rows), "checks": coverage,
              "break_counts": dict(Counter(b["type"] for b in breaks)), "breaks": breaks, "comparisons": comparisons,
              "completeness": "partial" if partial else "complete", "evaluability": "partial" if partial else "evaluable",
              "unresolved_issues": list(dict.fromkeys(issues)), "suggested_disposition": disposition, "disclaimer": DISCLAIMER}
    output["artifact"] = build_artifact(doc, output, producer="insurance-data-reconciler", artifact_type="insurance-data-reconciliation",
                                       completeness=output["completeness"], evaluability=output["evaluability"])
    if output["artifact"]["completeness"] != "complete" and disposition == "clean":
        output["suggested_disposition"] = "partial-not-evaluable"
        output["completeness"] = "partial"
        output["evaluability"] = "partial"
        output["artifact"] = build_artifact(doc, output, producer="insurance-data-reconciler", artifact_type="insurance-data-reconciliation")
    return output


def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/data_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try:
        doc = json.loads(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc), indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError) as exc:
        print(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
