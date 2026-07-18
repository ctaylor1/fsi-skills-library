#!/usr/bin/env python3
"""Deterministic skill-package planner for fsi-skill-authoring-assistant.

For each authoring build request this engine:
  1. Resolves the REQUIRED package components from the declared archetype + risk tier
     (a documented mapping, not judgment) and diffs them against what is present.
  2. Checks the proposed frontmatter metadata for completeness, allowed values, and
     tier/action-mode/approval consistency.
  3. Resolves the human approvals the tier owes and checks each readiness CLAIM against a
     recorded approval (an unbacked claim is an unsupported/unapproved assertion).
  4. Assigns a status by documented precedence and renders a review-ready authoring plan.

It NEVER publishes, registers, releases, or signs off a skill, never approves its own
output, and never fabricates metadata, sources, evaluations, or approval records. Only a
fully complete, template-faithful package with no unsupported claims becomes
`draft-package` (ready for owner review — approvals are surfaced as still owed, never
marked complete here). Operates on documented JSON + bundled fixtures only; no live calls.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the package-plan JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# ---- Build standards (versioned contract; see references/domain-rules.md) ----------------
ALWAYS_REQUIRED = [
    "SKILL.md", "references/source-map.md", "references/controls.md",
    "references/handoffs.md", "scripts/validate_input.py", "scripts/validate_output.py",
    "evals/evals.json", "CHANGELOG.md",
]
CALC_ARCHETYPES = {"Model & calculate", "Reconcile & validate"}
STANDING_NOTE = (
    "Draft skill package for owner review only; this skill does not publish, register, sign "
    "off, or release any skill into the catalog, does not approve its own output, and every "
    "package must pass validation and receive the required human approvals before release."
)
ALLOWED_ACTION_MODES = {
    "Read-only analysis", "Draft-only; no system-of-record change",
    "Scheduled read-only; alert only", "Approval-gated write or submission",
}
ALLOWED_HUMAN_APPROVAL = {"none", "external-delivery", "required"}
ALLOWED_SCHEDULED = {"no", "read-only-monitoring"}
REQUIRED_META_KEYS = [
    "aws-fsi-category", "aws-fsi-skill-type", "aws-fsi-risk-tier", "aws-fsi-archetype",
    "aws-fsi-agent-pattern", "aws-fsi-delivery-wave", "aws-fsi-action-mode",
    "aws-fsi-scheduled-agent", "aws-fsi-baseline-status", "aws-fsi-human-approval",
    "aws-fsi-data-classification", "aws-fsi-jurisdictions", "aws-fsi-owner",
    "aws-fsi-primary-user", "aws-fsi-version", "aws-fsi-recertification-date",
]
META_ALLOWED = {
    "aws-fsi-risk-tier": {"R1", "R2", "R3", "R4"},
    "aws-fsi-action-mode": ALLOWED_ACTION_MODES,
    "aws-fsi-human-approval": ALLOWED_HUMAN_APPROVAL,
    "aws-fsi-scheduled-agent": ALLOWED_SCHEDULED,
}
# Human approvals owed by tier (see references/controls.md release gates).
APPROVALS_BY_TIER = {
    "R1": ["product-owner", "domain-sme", "control-owner"],
    "R2": ["product-owner", "domain-sme", "control-owner"],
    "R3": ["product-owner", "domain-sme", "control-owner", "legal-compliance"],
    "R4": ["product-owner", "domain-sme", "control-owner", "legal-compliance", "model-risk"],
}
COMPLETE_APPROVAL_STATES = {"complete", "recorded", "approved"}
TEMPLATE_SECTIONS = [
    "frontmatter_block", "component_checklist", "source_map_plan",
    "approval_checklist", "standing_disclaimer",
]


def _required_components(s: dict) -> list[str]:
    comps = list(ALWAYS_REQUIRED)
    arch = s.get("archetype")
    if arch == "Draft & package":
        comps.append("assets/output-template.md")
    if arch in CALC_ARCHETYPES or s.get("has_deterministic_computation"):
        comps.append("scripts/calculate_or_transform.py")
    if s.get("applies_domain_rules") or arch in (CALC_ARCHETYPES | {"Analyze & review"}):
        comps.append("references/domain-rules.md")
    # stable, de-duplicated order
    out, seen = [], set()
    for c in comps:
        if c not in seen:
            out.append(c); seen.add(c)
    return out


def _metadata_check(s: dict) -> dict:
    meta = s.get("metadata") or {}
    missing = [k for k in REQUIRED_META_KEYS if k not in meta or str(meta.get(k)).strip() == ""]
    invalid = []
    for k, allowed in META_ALLOWED.items():
        if k in meta and meta[k] not in allowed:
            invalid.append(f"{k}={meta[k]!r}")
    consistency = _consistency(s, meta)
    # name/directory tie-out is validated in validate_input; re-affirm here for the plan.
    name, directory = s.get("name"), s.get("directory")
    if name and directory and Path(str(directory)).name != name:
        consistency.append(f"name {name!r} != directory basename {Path(str(directory)).name!r}")
    ok = not missing and not invalid and not consistency
    return {"ok": ok, "missing_keys": missing, "invalid_values": invalid, "consistency": consistency}


def _consistency(s: dict, meta: dict) -> list[str]:
    """Tier <-> action-mode <-> human-approval mutual consistency (RISK-TIERS.md)."""
    issues = []
    tier = meta.get("aws-fsi-risk-tier") or s.get("risk_tier")
    mode = meta.get("aws-fsi-action-mode") or s.get("action_mode")
    appr = meta.get("aws-fsi-human-approval") or s.get("human_approval")
    sched = meta.get("aws-fsi-scheduled-agent") or s.get("scheduled_agent")
    arch = meta.get("aws-fsi-archetype") or s.get("archetype")
    if tier in ("R1", "R2"):
        if appr not in ("external-delivery", None):
            issues.append(f"{tier} expects human-approval 'external-delivery', got {appr!r}")
        if mode not in ("Read-only analysis", "Draft-only; no system-of-record change", None):
            issues.append(f"{tier} action-mode {mode!r} not analytical/draft-only")
    if tier == "R3":
        if appr not in ("required", None):
            issues.append(f"R3 expects human-approval 'required', got {appr!r}")
        if mode == "Approval-gated write or submission":
            issues.append("R3 must not use approval-gated write (that is R4)")
    if tier == "R4":
        if appr not in ("required", None):
            issues.append(f"R4 expects human-approval 'required', got {appr!r}")
        if mode not in ("Approval-gated write or submission", None):
            issues.append(f"R4 action-mode {mode!r} must be approval-gated write or submission")
    if sched == "read-only-monitoring" and arch != "Monitor & alert":
        issues.append("scheduled read-only-monitoring is only permitted for 'Monitor & alert'")
    return issues


def _claims_index(s: dict) -> list[dict]:
    approvals = {a.get("approval_id"): a for a in (s.get("approvals") or [])}
    idx = []
    for c in s.get("claims") or []:
        aid = c.get("approval_id")
        rec = approvals.get(aid)
        supported = bool(rec) and str(rec.get("status", "")).lower() in COMPLETE_APPROVAL_STATES
        idx.append({"statement": c.get("statement"), "approval_id": aid, "supported": supported})
    return idx


def _render_frontmatter(meta: dict) -> str:
    lines = ["metadata:"]
    for k in REQUIRED_META_KEYS:
        if k in meta:
            lines.append(f'  {k}: "{meta[k]}"')
    return "\n".join(lines)


def plan_skill(s: dict) -> dict:
    name = s.get("name")
    required = _required_components(s)
    present = list(s.get("components_present") or [])
    missing = [c for c in required if c not in present]
    meta_chk = _metadata_check(s)
    claims = _claims_index(s)
    tier = (s.get("metadata") or {}).get("aws-fsi-risk-tier") or s.get("risk_tier")
    approvals_required = APPROVALS_BY_TIER.get(tier, APPROVALS_BY_TIER["R2"])
    approvals_status = [
        {"approval_id": a.get("approval_id"), "role": a.get("role"),
         "status": a.get("status", "pending")}
        for a in (s.get("approvals") or [])
    ]

    rec = {
        "skill_id": s.get("skill_id"),
        "name": name,
        "directory": s.get("directory"),
        "archetype": s.get("archetype"),
        "risk_tier": tier,
        "action_mode": (s.get("metadata") or {}).get("aws-fsi-action-mode") or s.get("action_mode"),
        "human_approval": (s.get("metadata") or {}).get("aws-fsi-human-approval") or s.get("human_approval"),
        "required_components": required,
        "components_present": present,
        "missing_components": missing,
        "metadata_check": meta_chk,
        "claims_index": claims,
        "approvals_required": approvals_required,
        "approvals_status": approvals_status,
        "frontmatter_block": _render_frontmatter(s.get("metadata") or {}),
        "template_sections": list(TEMPLATE_SECTIONS),
    }

    # ---- status precedence (see references/domain-rules.md) ----
    spec_incomplete = not all(s.get(k) for k in ("skill_id", "name", "directory", "archetype", "risk_tier"))
    if spec_incomplete or s.get("metadata") is None:
        rec["status"] = "needs-data"
        rec["blocked_reason"] = "spec or metadata block incomplete; cannot draft a package"
        rec["packageable"] = False
        return rec
    if not meta_chk["ok"]:
        rec["status"] = "metadata-incomplete"
        rec["blocked_reason"] = "frontmatter metadata missing keys, invalid values, or inconsistent tier/action-mode/approval"
        rec["packageable"] = False
        return rec
    if missing:
        rec["status"] = "missing-components"
        rec["blocked_reason"] = f"required components not present: {missing}"
        rec["packageable"] = False
        return rec
    if any(not c["supported"] for c in claims):
        rec["status"] = "unsupported-claim"
        rec["blocked_reason"] = "a readiness claim is not backed by a recorded approval"
        rec["packageable"] = False
        return rec
    rec["status"] = "draft-package"
    rec["packageable"] = True
    return rec


def plan(doc: dict) -> dict:
    records = [plan_skill(s) for s in doc["skills"]]
    summary = {
        "total": len(records),
        "draft_package": sum(1 for r in records if r["status"] == "draft-package"),
        "metadata_incomplete": sum(1 for r in records if r["status"] == "metadata-incomplete"),
        "missing_components": sum(1 for r in records if r["status"] == "missing-components"),
        "unsupported_claim": sum(1 for r in records if r["status"] == "unsupported-claim"),
        "needs_data": sum(1 for r in records if r["status"] == "needs-data"),
    }
    return {"build_standard_version": doc.get("build_standard_version"),
            "as_of_date": doc.get("as_of_date"),
            "packages": records, "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "requests_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(plan(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
