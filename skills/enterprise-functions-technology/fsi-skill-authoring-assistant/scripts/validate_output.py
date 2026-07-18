#!/usr/bin/env python3
"""Deterministic output validation for fsi-skill-authoring-assistant.

Enforces the R2 "Draft & package" guardrails before an authoring plan is handed to an owner
for review and authorized release:
  1. Status discipline: every record uses an allowed drafting status (never a
     released/published/registered/signed-off state).
  2. Template fidelity: a packageable record renders all required plan sections and its
     declared package has no missing required components.
  3. Metadata completeness: a packageable record's metadata_check passes (all required
     aws-fsi-* keys, allowed values, consistent tier/action-mode/approval).
  4. No unsupported/unapproved claims: every readiness claim is backed by a recorded
     approval, and the required approvals for the tier are all enumerated (as owed/pending
     is fine — never asserted complete here).
  5. No release/publish/self-approval language anywhere in the plan.
  6. The standing disclaimer (owner review; no publish/register/release; approvals owed) is
     present.

Fails closed on any miss so a defective or overreaching package plan cannot be presented as
ready-to-release. Operates on documented JSON + bundled fixtures only; no live calls.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUSES = {
    "draft-package", "metadata-incomplete", "missing-components",
    "unsupported-claim", "needs-data",
}
REQUIRED_TEMPLATE_SECTIONS = {
    "frontmatter_block", "component_checklist", "source_map_plan",
    "approval_checklist", "standing_disclaimer",
}
APPROVALS_BY_TIER = {
    "R1": {"product-owner", "domain-sme", "control-owner"},
    "R2": {"product-owner", "domain-sme", "control-owner"},
    "R3": {"product-owner", "domain-sme", "control-owner", "legal-compliance"},
    "R4": {"product-owner", "domain-sme", "control-owner", "legal-compliance", "model-risk"},
}
STANDING_NOTE = (
    "Draft skill package for owner review only; this skill does not publish, register, sign "
    "off, or release any skill into the catalog, does not approve its own output, and every "
    "package must pass validation and receive the required human approvals before release."
)
# Release / publish / self-approval overclaims — a draft plan must never assert these.
OVERCLAIM_PATTERNS = [
    r"\bpublished to (the )?catalog\b",
    r"\bregistered (the |this )?skill\b",
    r"\breleased to production\b",
    r"\breleased into the catalog\b",
    r"\bsigned off by\b",
    r"\bowner[- ]approved\b",
    r"\bapproved for release\b",
    r"\bcertified for release\b",
    r"\bready to ship\b",
    r"\bno (further )?review (needed|required)\b",
    r"\bvalidated and approved\b",
    r"\bself-approved\b",
    r"\bapproves its own\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    packages = doc.get("packages") or []
    if not packages:
        return ["package plan has no records"]

    for p in packages:
        sid = p.get("skill_id", "?")
        status = p.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{sid}: disallowed status {status!r} (release/publish states not permitted in drafting)")

        packageable = bool(p.get("packageable"))
        if packageable and status != "draft-package":
            errors.append(f"{sid}: packageable but status is {status!r} (only draft-package may be packageable)")
        if status == "draft-package" and not packageable:
            errors.append(f"{sid}: status draft-package but not marked packageable")

        if packageable:
            # 2. template fidelity + component completeness
            sections = set(p.get("template_sections") or [])
            missing_sections = REQUIRED_TEMPLATE_SECTIONS - sections
            if missing_sections:
                errors.append(f"{sid}: packageable but plan is missing template sections {sorted(missing_sections)}")
            miss = p.get("missing_components") or []
            if miss:
                errors.append(f"{sid}: packageable but required components missing {miss}")
            if not p.get("frontmatter_block"):
                errors.append(f"{sid}: packageable but frontmatter_block is empty")

            # 3. metadata completeness
            mc = p.get("metadata_check") or {}
            if not mc.get("ok"):
                errors.append(f"{sid}: packageable but metadata incomplete/invalid "
                              f"(missing {mc.get('missing_keys')}, invalid {mc.get('invalid_values')}, "
                              f"inconsistent {mc.get('consistency')})")

            # 4. no unsupported claims + required approvals enumerated
            for c in p.get("claims_index") or []:
                if not c.get("supported"):
                    errors.append(f"{sid}: unsupported readiness claim {c.get('statement')!r} "
                                  f"(approval {c.get('approval_id')!r} not recorded)")
            req = APPROVALS_BY_TIER.get(p.get("risk_tier"), APPROVALS_BY_TIER["R2"])
            enumerated = set(p.get("approvals_required") or [])
            if not req <= enumerated:
                errors.append(f"{sid}: approvals_required missing roles {sorted(req - enumerated)}")

    scan = json.dumps(packages) + " " + str(doc.get("narrative", ""))
    for pat in OVERCLAIM_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited release/approval-overclaim language detected: {m.group(0)!r} "
                          f"(this skill drafts only; it never publishes, releases, or self-approves)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "plan_example.json"
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
