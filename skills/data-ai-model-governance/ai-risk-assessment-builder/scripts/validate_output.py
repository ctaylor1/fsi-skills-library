#!/usr/bin/env python3
"""Deterministic output validation for ai-risk-assessment-builder.

Enforces the R3 "Draft & package" guardrails before an AI risk assessment pack is handed to a
human for review and adjudication:
  1. Template fidelity: all ten required risk domains are present.
  2. Source mapping: every domain is cited; every finding carries a source ref and a
     recommended remediation (no unsupported/unapproved assertion).
  3. Residual tie-out: each domain's declared residual_band equals the deterministic
     likelihood x impact matrix result; a High-residual domain carries an open finding; the
     overall rating equals the highest domain residual.
  4. Approval discipline: approval.status is `pending`, adjudication is required, and the
     routed approvers are consistent with the overall rating. Findings are `open` only.
  5. No autonomous-decision / approval / certification / deployment-clearance / finding-
     closure language.
  6. The standing disclaimer is present.

Fails closed on any miss so a defective or overreaching pack cannot be presented as a
completed or approved assessment.

Usage: python validate_output.py assessment.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_DOMAINS = {
    "data", "model", "fairness", "explainability", "security",
    "privacy", "third_party", "human_oversight", "resilience", "monitoring",
}
LEVEL_PTS = {"Low": 1, "Medium": 2, "High": 3}
CONTROL_WEIGHT = {"implemented": 1.0, "partial": 0.5, "missing": 0.0}
ORDER = {"Low": 0, "Medium": 1, "High": 2}
STANDING_NOTE = (
    "Draft AI risk assessment for human review only; this skill does not approve, certify, "
    "or authorize any AI system for deployment, makes no final risk determination, closes no "
    "findings, and every residual rating and finding requires review and adjudication by the "
    "accountable risk owner and approver before any decision."
)
ROUTING = {
    "High": ["Model Risk Committee", "Chief Risk Officer (or delegate)"],
    "Medium": ["AI Risk Officer", "Accountable Business Owner"],
    "Low": ["AI Risk Officer"],
}
DECISION_PATTERNS = [
    r"\bapproved for (production|deployment|use|release)\b",
    r"\bcleared (to|for) (deploy|deployment|production|launch|release)\b",
    r"\bauthorized for (deployment|production|release)\b",
    r"\bfit for (production|deployment)\b",
    r"\bno (further |additional )?(human )?review (is )?(required|needed)\b",
    r"\bwe (hereby )?certify\b",
    r"\brisk (is )?accepted\b",
    r"\bfinal (risk )?(determination|decision)\b",
    r"\bsign-?off (is )?complete\b",
    r"\bauto-?approved\b",
    r"\bgreen-?lit\b",
    r"\bfinding(s)? (closed|resolved|remediated|waived)\b",
    r"\bno action (required|needed)\b",
]


def _band(score: int) -> str:
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def _expected_residual(dom: dict) -> str:
    """Recompute the residual band from the domain's declared likelihood/impact/coverage.

    Preference order for control inputs: use the raw `controls` list when present (recompute
    coverage, unproven controls get no credit); otherwise fall back to a declared
    `coverage_tier`. This lets the screen re-derive residual from first principles.
    """
    like = LEVEL_PTS.get(dom.get("likelihood"), 0)
    imp = LEVEL_PTS.get(dom.get("impact"), 0)
    reduction = _reduction_from_domain(dom)
    residual_like = max(1, like - reduction) if like else 0
    return _band(residual_like * imp)


def _reduction_from_domain(dom: dict) -> int:
    controls = dom.get("controls")
    if isinstance(controls, list):
        applicable = [c for c in controls if isinstance(c, dict) and c.get("status") != "not_applicable"]
        if not applicable:
            pct = 0.0
        else:
            total = 0.0
            for c in applicable:
                proven = bool(c.get("evidence_ref"))
                total += CONTROL_WEIGHT.get(c.get("status"), 0.0) if proven else 0.0
            pct = total / len(applicable)
        return 2 if pct >= 0.80 else 1 if pct >= 0.50 else 0
    tier = dom.get("coverage_tier")
    return {"Strong": 2, "Moderate": 1, "Weak": 0, "None": 0}.get(tier, 0)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    domains = doc.get("domains") or []
    if not domains:
        return ["assessment output has no domain scoring"]

    present = {d.get("domain") for d in domains}
    for d in sorted(REQUIRED_DOMAINS - present):
        errors.append(f"missing required risk domain '{d}' (template fidelity)")

    high_domains = set()
    computed_overall = "Low"
    for dom in domains:
        name = dom.get("domain", "?")
        if not dom.get("citations"):
            errors.append(f"{name}: no citations (unsupported risk assertion - every domain must map to a source)")
        declared = dom.get("residual_band")
        expected = _expected_residual(dom)
        if declared != expected:
            errors.append(f"{name}: residual_band {declared!r} != expected {expected!r} (matrix tie-out)")
        band = declared if declared in ORDER else expected
        if band == "High":
            high_domains.add(name)
        if ORDER.get(band, 0) > ORDER[computed_overall]:
            computed_overall = band

    findings = doc.get("findings") or []
    finding_domains = {f.get("domain") for f in findings}
    for f in findings:
        fid = f.get("finding_id", "?")
        if not f.get("recommended_remediation"):
            errors.append(f"{fid} ({f.get('domain')}): finding missing recommended_remediation")
        if not f.get("source_refs"):
            errors.append(f"{fid} ({f.get('domain')}): finding missing source reference (unsupported assertion)")
        if f.get("status") != "open":
            errors.append(f"{fid} ({f.get('domain')}): finding status must be 'open' (this skill does not close findings)")
    for name in sorted(high_domains):
        if name not in finding_domains:
            errors.append(f"{name}: residual High but no open finding (must be surfaced for adjudication)")

    declared_overall = doc.get("overall_residual_rating")
    if declared_overall != computed_overall:
        errors.append(f"overall_residual_rating {declared_overall!r} != expected {computed_overall!r} (highest domain residual)")

    approval = doc.get("approval") or {}
    if approval.get("status") != "pending":
        errors.append(f"approval status must be 'pending' (this skill never approves/certifies a system), got {approval.get('status')!r}")
    if not approval.get("adjudication_required"):
        errors.append("approval.adjudication_required must be true (R3 mandatory human adjudication)")
    approvers = approval.get("required_approvers") or []
    if not approvers:
        errors.append("approval.required_approvers is empty (no routing)")
    else:
        exp_route = ROUTING.get(computed_overall, [])
        if set(approvers) != set(exp_route):
            errors.append(f"required_approvers {approvers} != expected {exp_route} for overall {computed_overall!r}")

    scan = json.dumps(domains) + " " + json.dumps(findings) + " " + str(doc.get("narrative", ""))
    for pat in DECISION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited autonomous-decision language detected: {m.group(0)!r} (this skill never approves/certifies/authorizes deployment or closes findings)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
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
