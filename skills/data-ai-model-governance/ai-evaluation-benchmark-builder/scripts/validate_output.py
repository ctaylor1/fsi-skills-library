#!/usr/bin/env python3
"""Deterministic output validation for ai-evaluation-benchmark-builder.

Enforces the R3 "Draft & package" guardrails before an evaluation-benchmark package is handed
to model-risk governance for review and approval:
  1. Template fidelity / completeness: required top-level sections and per-evaluation fields
     are present; every dimension is in the approved 7-dimension taxonomy.
  2. Coverage integrity: the coverage matrix is internally consistent, and a package marked
     ready-for-governance-review truly has complete coverage and every eval ready.
  3. No unsupported/unapproved claims: any acceptance threshold or baseline marked `approved`
     must cite a source; a `ready-for-review` eval must be fully sourced (approved), sample-
     adequate, and direction-consistent - no invented or unsourced numbers pass as ready.
  4. No autonomous decision/certification: the skill never self-approves governance and never
     asserts the model passed / is compliant / is approved for production / is certified.
  5. Required approvals: governance_approval is `pending` and reviewer_signoff_required is true.
  6. The standing disclaimer is present.

Fails closed on any miss so a defective or overreaching benchmark cannot be presented as
approved, complete, or a release decision.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

KNOWN_DIMENSIONS = {"task", "trigger", "regression", "safety", "robustness", "latency", "cost"}
MIN_SAMPLE = {
    "task": 100, "trigger": 50, "regression": 100, "safety": 200,
    "robustness": 100, "latency": 30, "cost": 30,
}
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
ALLOWED_STATUS = {
    "ready-for-review", "needs-calibration", "insufficient-sample",
    "direction-mismatch", "needs-data",
}
REQUIRED_TOP = ("system_under_eval", "evaluations", "coverage", "approvals", "standing_note")
REQUIRED_EVAL = ("eval_id", "dimension", "metric", "sample_size", "status", "acceptance", "baseline")

STANDING_NOTE = (
    "Draft evaluation benchmark for human review only; this skill does not run the "
    "evaluations, does not score or certify the model, and makes no go/no-go, release, or "
    "compliance determination"
)

# Language that would turn a draft plan into a determination / certification / release call.
DETERMINATION_PATTERNS = [
    r"\bapproved for (production|release|deployment|go-live)\b",
    r"\bcleared for (production|release|deployment|go-live)\b",
    r"\bcertified (safe|compliant|fair|unbiased|for release)\b",
    r"\bthe model (passed|failed|meets all requirements)\b",
    r"\bmodel is (compliant|production-ready|fit for purpose)\b",
    r"\bfully compliant\b", r"\bproduction-ready\b", r"\bfit for purpose\b",
    r"\bgo/?no-?go decision\b", r"\bwe recommend (release|deployment|go-live)\b",
    r"\bcompliance determination\b",
    r"\bno further (evaluation|review|validation) (is )?(needed|required)\b",
    r"\bgovernance sign-?off (is )?complete\b",
]


def _direction_ok(metric, operator):
    d = METRIC_DIRECTION.get(metric)
    if not d or operator in (None, "=="):
        return True
    return operator in HIGHER_OPS if d == "higher" else operator in LOWER_OPS


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level section '{k}'")
    if errors:
        return errors

    evals = doc.get("evaluations") or []
    if not evals:
        return ["benchmark output has no evaluations"]

    for e in evals:
        eid = e.get("eval_id", "?")
        for k in REQUIRED_EVAL:
            if k not in e:
                errors.append(f"{eid}: missing evaluation field '{k}'")
        dim = e.get("dimension")
        if dim not in KNOWN_DIMENSIONS:
            errors.append(f"{eid}: unknown evaluation dimension {dim!r} (not in approved 7-dimension taxonomy)")
        status = e.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{eid}: invalid status {status!r}")

        acc = e.get("acceptance") or {}
        bl = e.get("baseline") or {}
        # A value marked 'approved' must cite a source (no unsupported/unapproved claim).
        for label, spec in (("threshold", acc), ("baseline", bl)):
            if spec.get("provenance") == "approved" and not spec.get("source_id"):
                errors.append(f"{eid}: {label} marked 'approved' without a source citation (unsupported claim)")
            if spec.get("value") not in (None, "") and spec.get("provenance") not in ("approved", "proposed"):
                errors.append(f"{eid}: {label} asserts value {spec.get('value')!r} without an approved source (unsupported claim)")

        # Strict invariants for anything presented as ready.
        if status == "ready-for-review":
            if not e.get("dataset_ref"):
                errors.append(f"{eid}: ready-for-review but no representative dataset_ref")
            if acc.get("provenance") != "approved":
                errors.append(f"{eid}: ready-for-review but acceptance threshold not approved-sourced (provenance {acc.get('provenance')!r})")
            if bl.get("provenance") != "approved":
                errors.append(f"{eid}: ready-for-review but baseline not approved-sourced (provenance {bl.get('provenance')!r})")
            min_n = MIN_SAMPLE.get(dim, 0)
            if int(e.get("sample_size") or 0) < min_n:
                errors.append(f"{eid}: ready-for-review but sample_size {e.get('sample_size')} below minimum {min_n} for {dim}")
            if not _direction_ok(e.get("metric"), acc.get("operator")):
                errors.append(f"{eid}: ready-for-review but acceptance operator {acc.get('operator')!r} contradicts metric direction")

    # Coverage integrity.
    cov = doc.get("coverage") or {}
    missing = cov.get("missing_required")
    if isinstance(missing, list) and bool(missing) == bool(cov.get("complete")):
        errors.append(f"coverage.complete={cov.get('complete')} inconsistent with missing_required={missing}")

    # A ready-for-governance-review package must be genuinely complete and fully ready.
    if doc.get("benchmark_status") == "ready-for-governance-review":
        if not cov.get("complete"):
            errors.append("benchmark_status 'ready-for-governance-review' but coverage is incomplete")
        if any(e.get("status") != "ready-for-review" for e in evals):
            errors.append("benchmark_status 'ready-for-governance-review' but not every evaluation is ready-for-review")

    # Required approvals: the skill proposes; it never self-approves.
    appr = doc.get("approvals") or {}
    if appr.get("governance_approval") != "pending":
        errors.append(f"governance_approval must be 'pending'; the skill cannot self-approve governance (got {appr.get('governance_approval')!r})")
    if appr.get("reviewer_signoff_required") is not True:
        errors.append("reviewer_signoff_required must be true")

    # Determination / certification / release language screen.
    scan = json.dumps(evals) + " " + json.dumps(doc.get("approvals") or {}) + " " + str(doc.get("narrative", ""))
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited determination/certification language detected: {m.group(0)!r} (this skill drafts a plan; it never decides, certifies, or releases)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "benchmark_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
