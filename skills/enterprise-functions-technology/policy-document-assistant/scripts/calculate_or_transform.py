#!/usr/bin/env python3
"""Deterministic policy-draft assembly engine for policy-document-assistant.

Assembles a controlled policy/procedure DRAFT from a build request:
  - maps every normative clause to an APPROVED requirement in the register (any clause that
    cannot be mapped is recorded as an unsupported assertion, never silently accepted);
  - lays the clauses into the canonical controlled-policy template sections;
  - computes the next version deterministically from the change type;
  - computes the next-review date from the proposed effective date and the policy tier;
  - produces a change summary (added / modified / removed) against the prior version;
  - opens approval slots for each required role (pending — approvals are recorded by humans).

It NEVER publishes, activates, files, or makes a policy effective, and never invents a
requirement to justify a clause. Output is a draft for human review only.

Usage:
  python calculate_or_transform.py request.json   # prints the assembled draft JSON
  python calculate_or_transform.py --selftest      # runs invariant checks on the fixture
Exit 0 on success; 1 if --selftest finds an invariant error.
"""
from __future__ import annotations
import calendar, json, sys
from datetime import date
from pathlib import Path

# Canonical controlled-policy sections (order matters). See references/domain-rules.md.
REQUIRED_SECTIONS = [
    ("document-control", "Document Control"),
    ("purpose", "Purpose"),
    ("scope", "Scope"),
    ("policy-statements", "Policy Statements"),
    ("roles-responsibilities", "Roles and Responsibilities"),
    ("related-documents", "Related Documents and Source Mapping"),
    ("review-version-history", "Review and Version History"),
    ("approvals", "Approvals"),
]
OPTIONAL_SECTIONS = [
    ("definitions", "Definitions"),
    ("exceptions-escalation", "Exceptions and Escalation"),
]
SECTION_HEADINGS = dict(REQUIRED_SECTIONS + OPTIONAL_SECTIONS)
# Sections whose bodies are auto-generated rather than sourced from clauses.
GENERATED_SECTIONS = {"document-control", "related-documents", "review-version-history", "approvals"}

TIER_REVIEW_MONTHS = {"tier-1": 12, "tier-2": 24, "tier-3": 36}
DEFAULT_REVIEW_MONTHS = 12
DEFAULT_APPROVALS = ["owner", "legal", "compliance"]
STANDING_NOTE = (
    "Draft policy for human review only; not published, activated, or made effective. "
    "Owner, legal, and compliance approval and publication into the policy management "
    "system of record are separate human actions."
)


def bump_version(version: str, change_type: str) -> str:
    major, minor = (int(x) for x in str(version).split(".")[:2])
    if change_type == "major":
        return f"{major + 1}.0"
    if change_type == "minor":
        return f"{major}.{minor + 1}"
    return f"{major}.{minor}"  # editorial: no version bump


def add_months(iso_date: str, months: int) -> str:
    y, m, d = (int(x) for x in iso_date.split("-"))
    total = y * 12 + (m - 1) + months
    ny, nm0 = divmod(total, 12)
    nm = nm0 + 1
    last = calendar.monthrange(ny, nm)[1]
    return date(ny, nm, min(d, last)).isoformat()


def _resolve_sources(req_ids, reg_by_id):
    """Return (approved_sources, problems) for a normative clause's req_ids."""
    sources, problems = [], []
    for rid in req_ids or []:
        r = reg_by_id.get(rid)
        if r is None:
            problems.append(f"{rid}: not in requirements register")
        elif r.get("status") != "approved":
            problems.append(f"{rid}: status {r.get('status')!r} is not 'approved'")
        elif not r.get("source"):
            problems.append(f"{rid}: register entry has no source")
        else:
            sources.append({"req_id": rid, "source": r["source"],
                            "owner": r.get("owner"), "status": "approved"})
    return sources, problems


def _change_summary(clauses, prior_clauses):
    cur = {c.get("clause_id"): (c.get("text") or "").strip() for c in clauses}
    pri = {c.get("clause_id"): (c.get("text") or "").strip() for c in (prior_clauses or [])}
    added = sorted(set(cur) - set(pri))
    removed = sorted(set(pri) - set(cur))
    modified = sorted(cid for cid in (set(cur) & set(pri)) if cur[cid] != pri[cid])
    return {
        "added": added, "modified": modified, "removed": removed,
        "normative_count": sum(1 for c in clauses if c.get("normative")),
        "informational_count": sum(1 for c in clauses if not c.get("normative")),
        "prior_version_provided": bool(prior_clauses),
    }


def assemble(doc: dict) -> dict:
    pol = doc.get("policy") or {}
    reg_by_id = {r.get("req_id"): r for r in (doc.get("requirements_register") or [])}
    clauses = pol.get("clauses") or []
    change_type = pol.get("change_type", "editorial")
    prior_version = str(pol.get("current_version", "0.0"))
    new_version = bump_version(prior_version, change_type)

    tier = pol.get("tier")
    interval = TIER_REVIEW_MONTHS.get(tier, DEFAULT_REVIEW_MONTHS)
    eff = pol.get("proposed_effective_date")
    next_review = add_months(eff, interval) if eff else None

    # Group clauses into sections; resolve sources for normative clauses.
    section_clauses: dict[str, list] = {}
    source_mapping, unsupported = [], []
    for c in clauses:
        sid = c.get("section_id")
        entry = {"clause_id": c.get("clause_id"), "heading": c.get("heading"),
                 "text": c.get("text"), "normative": bool(c.get("normative"))}
        if c.get("normative"):
            sources, problems = _resolve_sources(c.get("req_ids"), reg_by_id)
            entry["sources"] = sources
            source_mapping.append({"clause_id": c.get("clause_id"),
                                   "req_ids": c.get("req_ids") or [],
                                   "sources": [s["source"] for s in sources]})
            if not sources:
                entry["unsupported"] = True
                unsupported.append({"clause_id": c.get("clause_id"),
                                    "reason": "; ".join(problems) or "no approved requirement mapped"})
        section_clauses.setdefault(sid, []).append(entry)

    # Ordered section list: required (always) + optional (only if clauses present).
    present_optional = [(sid, h) for sid, h in OPTIONAL_SECTIONS if section_clauses.get(sid)]
    ordered = REQUIRED_SECTIONS[:4] + present_optional[:1] + REQUIRED_SECTIONS[4:5] \
        + present_optional[1:] + REQUIRED_SECTIONS[5:]

    # Related-documents: unique cited sources + prior version reference.
    cited = []
    for m in source_mapping:
        for s in m["sources"]:
            if s not in cited:
                cited.append(s)
    if doc.get("prior_version_ref"):
        cited.append(doc["prior_version_ref"])

    change_summary = _change_summary(clauses, pol.get("prior_clauses"))

    sections = []
    for sid, heading in ordered:
        sec = {"section_id": sid, "heading": heading}
        if sid == "document-control":
            sec["body"] = {
                "policy_id": pol.get("policy_id"), "title": pol.get("title"),
                "policy_type": pol.get("policy_type"), "tier": tier,
                "version": new_version, "prior_version": prior_version,
                "change_type": change_type, "owner": pol.get("owner"),
                "classification": pol.get("classification"),
                "proposed_effective_date": eff, "next_review_date": next_review,
            }
        elif sid == "related-documents":
            sec["sources"] = cited
        elif sid == "review-version-history":
            sec["body"] = {"prior_version": prior_version, "new_version": new_version,
                           "change_type": change_type, "last_review_date": pol.get("last_review_date"),
                           "change_summary": change_summary}
        elif sid == "approvals":
            sec["required_roles"] = doc.get("approvals_required") or DEFAULT_APPROVALS
        else:
            sec["clauses"] = section_clauses.get(sid, [])
        sections.append(sec)

    approvals = [{"role": r, "approver": None, "date": None, "status": "pending"}
                 for r in (doc.get("approvals_required") or DEFAULT_APPROVALS)]

    return {
        "config_version": doc.get("config_version"),
        "policy_id": pol.get("policy_id"), "title": pol.get("title"),
        "policy_type": pol.get("policy_type"), "tier": tier,
        "prior_version": prior_version, "new_version": new_version,
        "change_type": change_type, "owner": pol.get("owner"),
        "classification": pol.get("classification"),
        "proposed_effective_date": eff, "next_review_date": next_review,
        "sections": sections,
        "source_mapping": source_mapping,
        "unsupported_clauses": unsupported,
        "change_summary": change_summary,
        "approvals_required": doc.get("approvals_required") or DEFAULT_APPROVALS,
        "approvals": approvals,
        "standing_note": STANDING_NOTE,
    }


def _selftest() -> int:
    p = Path(__file__).resolve().parents[1] / "evals" / "files" / "policy_request_example.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    draft = assemble(doc)
    errors = []
    present = {s["section_id"] for s in draft["sections"]}
    for sid, _ in REQUIRED_SECTIONS:
        if sid not in present:
            errors.append(f"required section {sid!r} not assembled")
    if draft["new_version"] != "2.4":
        errors.append(f"expected new_version 2.4, got {draft['new_version']}")
    if draft["next_review_date"] != "2027-09-01":
        errors.append(f"expected next_review_date 2027-09-01, got {draft['next_review_date']}")
    if draft["unsupported_clauses"]:
        errors.append(f"golden request should have no unsupported clauses, got {draft['unsupported_clauses']}")
    cs = draft["change_summary"]
    if cs["added"] != ["C-6", "C-8"] or cs["modified"] != ["C-3"] or cs["removed"] != []:
        errors.append(f"unexpected change summary: {cs}")
    if any(a["status"] != "pending" for a in draft["approvals"]):
        errors.append("assembled draft must open approvals as pending")
    for e in errors:
        print("ERROR", e)
    print(f"self-test: {len(errors)} error(s)")
    return 1 if errors else 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
