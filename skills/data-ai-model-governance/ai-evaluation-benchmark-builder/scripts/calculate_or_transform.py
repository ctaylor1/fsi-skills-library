#!/usr/bin/env python3
"""Deterministic evaluation-benchmark builder for ai-evaluation-benchmark-builder.

For each requested evaluation it: confirms the dimension is in the approved taxonomy, checks a
representative dataset and metric are named, resolves the PROVENANCE of every acceptance
threshold and baseline against the approved-source list (approved vs proposed vs missing),
checks the metric/operator direction is consistent, checks the sample size against the
documented per-dimension minimum, and assigns a deterministic status. It then builds the
coverage matrix for the system's risk rating and packages the whole benchmark as a DRAFT for
model-risk-governance review.

It NEVER runs/executes an evaluation, never scores the model, never invents a threshold or
baseline number, never marks the model passed/compliant/approved, and never self-approves the
benchmark. `governance_approval` is always emitted as `pending`; every asserted threshold or
baseline is traceable to an approved source or explicitly flagged `proposed` for calibration.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the benchmark package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft evaluation benchmark for human review only; this skill does not run the "
    "evaluations, does not score or certify the model, and makes no go/no-go, release, or "
    "compliance determination - every threshold and baseline must be approved by model risk "
    "governance before use."
)

KNOWN_DIMENSIONS = {"task", "trigger", "regression", "safety", "robustness", "latency", "cost"}

# Documented minimum sample sizes per dimension (versioned methodology, not judgment).
MIN_SAMPLE = {
    "task": 100, "trigger": 50, "regression": 100, "safety": 200,
    "robustness": 100, "latency": 30, "cost": 30,
}

# Required coverage by the system's inherent risk rating (versioned methodology).
REQUIRED_COVERAGE = {
    "High": {"task", "trigger", "regression", "safety", "robustness", "latency", "cost"},
    "Medium": {"task", "regression", "safety", "latency"},
    "Low": {"task", "regression"},
}

# Metric direction: "higher" = higher is better (acceptance operator should be >= or >);
# "lower" = lower is better (operator should be <= or <). Unknown metrics skip the check.
METRIC_DIRECTION = {
    "accuracy": "higher", "f1": "higher", "exact_match": "higher", "pass_rate": "higher",
    "groundedness": "higher", "refusal_accuracy": "higher",
    "trigger_precision": "higher", "trigger_recall": "higher", "routing_accuracy": "higher",
    "toxicity_rate": "lower", "jailbreak_success_rate": "lower", "pii_leak_rate": "lower",
    "hallucination_rate": "lower", "prompt_injection_success_rate": "lower",
    "robust_accuracy_drop": "lower", "adversarial_success_rate": "lower",
    "p50_latency_ms": "lower", "p95_latency_ms": "lower",
    "cost_per_1k_tokens_usd": "lower", "cost_per_task_usd": "lower",
}
HIGHER_OPS = {">=", ">"}
LOWER_OPS = {"<=", "<"}


def _provenance(spec, source_ids):
    """Resolve a threshold/baseline spec to (provenance, value, operator, source_id)."""
    if not isinstance(spec, dict) or spec.get("value") in (None, ""):
        return "missing", None, spec.get("operator") if isinstance(spec, dict) else None, None
    sid = spec.get("source_id")
    prov = "approved" if (sid and sid in source_ids) else "proposed"
    return prov, spec.get("value"), spec.get("operator"), sid


def _direction_ok(metric, operator):
    d = METRIC_DIRECTION.get(metric)
    if not d or operator in (None, "=="):
        return True  # unknown metric or equality target -> not checked
    if d == "higher":
        return operator in HIGHER_OPS
    return operator in LOWER_OPS


def build_eval(r, source_ids):
    eid = r.get("eval_id")
    dim = r.get("dimension")
    metric = r.get("metric")
    dataset = r.get("dataset_ref")
    sample = int(r.get("sample_size") or 0)
    notes = []

    th_prov, th_val, th_op, th_sid = _provenance(r.get("threshold"), source_ids)
    bl_prov, bl_val, _, bl_sid = _provenance(r.get("baseline"), source_ids)

    citations = []
    if th_sid:
        citations.append(f"source:{th_sid}#threshold")
    if bl_sid:
        citations.append(f"source:{bl_sid}#baseline")
    if dataset:
        citations.append(f"data-catalog:{dataset}")

    rec = {
        "eval_id": eid,
        "dimension": dim,
        "metric": metric,
        "metric_direction": METRIC_DIRECTION.get(metric, "unknown"),
        "dataset_ref": dataset,
        "sample_size": sample,
        "min_sample": MIN_SAMPLE.get(dim),
        "acceptance": {"operator": th_op, "value": th_val, "provenance": th_prov, "source_id": th_sid},
        "baseline": {"value": bl_val, "provenance": bl_prov, "source_id": bl_sid},
        "citations": citations,
        "notes": notes,
    }

    # Deterministic status precedence (fail closed; never invent numbers).
    if dim not in KNOWN_DIMENSIONS:
        notes.append(f"dimension {dim!r} not in approved taxonomy")
        rec["status"] = "needs-data"
        return rec
    if not dataset or not metric:
        if not dataset:
            notes.append("no representative dataset (dataset_ref)")
        if not metric:
            notes.append("no metric named")
        rec["status"] = "needs-data"
        return rec
    if not _direction_ok(metric, th_op):
        notes.append(f"acceptance operator {th_op!r} contradicts '{METRIC_DIRECTION.get(metric)}-is-better' metric {metric!r}")
        rec["status"] = "direction-mismatch"
        return rec
    min_n = MIN_SAMPLE.get(dim, 0)
    if sample < min_n:
        notes.append(f"sample_size {sample} below documented minimum {min_n} for {dim}")
        rec["status"] = "insufficient-sample"
        return rec
    if th_prov != "approved" or bl_prov != "approved":
        if th_prov != "approved":
            notes.append("acceptance threshold not traced to an approved source (proposed placeholder; calibrate before use)")
        if bl_prov != "approved":
            notes.append("baseline not traced to an approved source (proposed placeholder; calibrate before use)")
        rec["status"] = "needs-calibration"
        return rec

    notes.append("dataset, approved acceptance threshold, approved baseline, direction, and sample size all satisfied")
    rec["status"] = "ready-for-review"
    return rec


def coverage(reqs_dims, risk_rating):
    required = REQUIRED_COVERAGE.get(risk_rating, set())
    present = {d for d in reqs_dims if d in KNOWN_DIMENSIONS}
    missing = sorted(required - present)
    return {
        "risk_rating": risk_rating,
        "required": sorted(required),
        "present": sorted(present),
        "missing_required": missing,
        "complete": not missing,
    }


def build(doc: dict) -> dict:
    sue = doc.get("system_under_eval") or {}
    source_ids = {s.get("source_id") for s in (doc.get("approved_sources") or []) if s.get("source_id")}
    evals = [build_eval(r, source_ids) for r in doc.get("requirements") or []]

    cov = coverage([e["dimension"] for e in evals], sue.get("risk_rating"))
    all_ready = bool(evals) and all(e["status"] == "ready-for-review" for e in evals)
    benchmark_status = "ready-for-governance-review" if (all_ready and cov["complete"]) else "draft-incomplete"

    def _count(s):
        return sum(1 for e in evals if e["status"] == s)

    summary = {
        "total": len(evals),
        "ready_for_review": _count("ready-for-review"),
        "needs_calibration": _count("needs-calibration"),
        "insufficient_sample": _count("insufficient-sample"),
        "direction_mismatch": _count("direction-mismatch"),
        "needs_data": _count("needs-data"),
    }

    return {
        "spec_version": doc.get("spec_version"),
        "as_of_date": doc.get("as_of_date"),
        "system_under_eval": {
            "model_id": sue.get("model_id"),
            "name": sue.get("name"),
            "version": sue.get("version"),
            "use_case": sue.get("use_case"),
            "risk_rating": sue.get("risk_rating"),
            "registry_ref": sue.get("registry_ref"),
        },
        "evaluations": evals,
        "coverage": cov,
        "benchmark_status": benchmark_status,
        "approvals": {
            "governance_approval": "pending",
            "reviewer_signoff_required": True,
            "approver_role": "Model Risk Governance / MRM",
        },
        "summary": summary,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "benchmark_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
