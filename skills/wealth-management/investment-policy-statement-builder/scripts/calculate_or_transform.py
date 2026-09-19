#!/usr/bin/env python3
"""Assemble a substantive sourced IPS mandate. No risk rating or approval is inferred."""

import json
import sys
from pathlib import Path
from wealth_contract import make_output, validate_envelope
from planning_support import Check, all_sources

SKILL = "investment-policy-statement-builder"
SECTIONS = [
    ("purpose", "Purpose and Scope"),
    ("governance", "Governance and Roles"),
    ("objectives", "Investment Objectives"),
    ("risk_profile", "Risk Profile and Governing Constraints"),
    ("time_horizon", "Time Horizon"),
    ("liquidity", "Liquidity Requirements"),
    ("tax", "Tax Considerations"),
    ("constraints", "Constraints and Restrictions"),
    ("allocation", "Strategic Asset Allocation"),
    ("rebalancing", "Rebalancing Policy"),
    ("monitoring", "Benchmarks and Monitoring"),
    ("approvals", "Approvals and Effective Date"),
    ("disclosures", "Disclosures"),
]


def describe(value, level=0):
    """Render supplied substantive fields and citations, including explicit absent evidence."""
    if value is None:
        return "Not supplied — requires human completion."
    if isinstance(value, list):
        return (
            "\n".join("- " + describe(item, level + 1).replace("\n", "\n  ") for item in value)
            if value
            else "Explicitly recorded as none."
        )
    if isinstance(value, dict):
        return (
            "\n".join(f"**{k.replace('_', ' ').capitalize()}**: {describe(v, level + 1)}" for k, v in value.items())
            if value
            else "Not supplied — requires human completion."
        )
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def inspect(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors, [], {}
    c = Check(doc)
    c.upstream()
    c.choice(doc.get("currency"), "currency", {"USD"})
    c.text(doc.get("ips_id"), "ips_id")
    revision = c.number(doc.get("revision"), "revision", 1, 100000, True)
    if "supersedes_artifact_id" not in doc:
        c.gap("supersedes_artifact_id", "Record the prior artifact ID or explicit null for first draft")
    elif doc["supersedes_artifact_id"] is not None:
        c.text(doc["supersedes_artifact_id"], "supersedes_artifact_id")
    if revision is not None:
        if revision > 1 and not doc.get("supersedes_artifact_id"):
            c.gap(
                "supersedes_artifact_id",
                "A refresh revision requires the prior IPS artifact ID",
                "revision-lineage-gap",
            )
        elif revision == 1 and doc.get("supersedes_artifact_id") is not None:
            c.gap(
                "supersedes_artifact_id",
                "First-draft revision 1 must use explicit null lineage; a refresh uses a later revision",
                "revision-lineage-conflict",
            )
    template = c.obj(doc.get("template"), "template")
    for key in ["template_id", "version"]:
        c.text(template.get(key), "template." + key)
    keys = c.strings(template.get("required_sections"), "template.required_sections")
    if keys and keys != [k for k, _ in SECTIONS]:
        c.gap(
            "template.required_sections",
            "Template must declare the 13 supported sections in order; reconcile with its owner",
            "template-mismatch",
        )
    c.sources(template, "template")
    mandate = c.obj(doc.get("mandate"), "mandate")
    blocks = {}
    for key, _ in SECTIONS:
        if key in {"allocation", "approvals"}:
            continue
        block = c.obj(mandate.get(key), "mandate." + key)
        blocks[key] = block
        c.sources(block, "mandate." + key)
    required_text = {
        "purpose": ["text"],
        "governance": ["decision_authority", "capacity_basis"],
        "objectives": ["return_objective", "spending_objective"],
        "risk_profile": ["profile_artifact_id", "governing_constraint", "human_reviewer", "assessment_reference"],
        "time_horizon": ["stage"],
        "tax": ["assumptions_version", "limitations"],
        "rebalancing": ["frequency", "tax_cost_constraints", "exception_owner"],
        "monitoring": ["portfolio_benchmark", "frequency", "owner"],
        "disclosures": ["text", "version"],
    }
    for key, fields in required_text.items():
        for field in fields:
            c.text(blocks[key].get(field), f"mandate.{key}.{field}")
    accounts = c.strings(blocks["purpose"].get("account_ids"), "mandate.purpose.account_ids")
    parties = c.rows(blocks["governance"].get("parties"), "mandate.governance.parties")
    party_roles = set()
    for i, row in enumerate(parties):
        path = f"mandate.governance.parties[{i}]"
        for key in ["party_id", "role", "responsibility"]:
            c.text(row.get(key), path + "." + key)
        c.sources(row, path)
        if isinstance(row.get("party_id"), str) and isinstance(row.get("role"), str):
            identity = (row["party_id"], row["role"])
            if identity in party_roles:
                c.errors.append(path + " repeats a governance party/role assignment")
            party_roles.add(identity)
    objectives = c.rows(blocks["objectives"].get("items"), "mandate.objectives.items")
    c.unique(objectives, "objective_id", "mandate.objectives.items")
    for i, row in enumerate(objectives):
        path = f"mandate.objectives.items[{i}]"
        c.text(row.get("description"), path + ".description")
        c.number(row.get("priority"), path + ".priority", 1, 100, True)
        c.sources(row, path)
    dims = c.rows(blocks["risk_profile"].get("dimensions"), "mandate.risk_profile.dimensions")
    dim_ids = c.unique(dims, "dimension", "mandate.risk_profile.dimensions")
    expected = {"willingness", "loss-capacity", "liquidity", "horizon", "experience", "constraints"}
    if dim_ids != expected:
        c.gap(
            "mandate.risk_profile.dimensions",
            "Preserve all six separately assessed risk dimensions",
            "risk-profile-incomplete",
        )
    for i, row in enumerate(dims):
        path = f"mandate.risk_profile.dimensions[{i}]"
        c.choice(row.get("dimension"), path + ".dimension", expected)
        c.text(row.get("assessment"), path + ".assessment")
        c.sources(row, path)
    conflicts = c.rows(
        blocks["risk_profile"].get("unresolved_findings"), "mandate.risk_profile.unresolved_findings", True
    )
    for i, row in enumerate(conflicts):
        path = f"mandate.risk_profile.unresolved_findings[{i}]"
        c.text(row.get("description"), path + ".description")
        c.sources(row, path)
        c.gap(
            path,
            "Unresolved upstream risk finding must remain visible for human adjudication",
            "unresolved-risk-finding",
        )
    c.number(blocks["time_horizon"].get("months"), "mandate.time_horizon.months", 0, 1440, True)
    for key in ["reserve_amount", "annual_distribution"]:
        c.amount(blocks["liquidity"].get(key), "mandate.liquidity." + key)
    events = c.rows(blocks["liquidity"].get("events"), "mandate.liquidity.events", True)
    c.unique(events, "event_id", "mandate.liquidity.events")
    for i, row in enumerate(events):
        path = f"mandate.liquidity.events[{i}]"
        c.date(row.get("date"), path + ".date")
        c.amount(row.get("amount"), path + ".amount")
        c.text(row.get("purpose"), path + ".purpose")
        c.sources(row, path)
    taxes = c.rows(blocks["tax"].get("account_treatments"), "mandate.tax.account_treatments")
    taxids = c.unique(taxes, "account_id", "mandate.tax.account_treatments")
    if set(accounts) != taxids:
        c.gap(
            "mandate.tax.account_treatments",
            "Tax treatment must cover exactly the mandate account scope",
            "account-scope-mismatch",
        )
    for i, row in enumerate(taxes):
        path = f"mandate.tax.account_treatments[{i}]"
        for key in ["registration", "treatment"]:
            c.text(row.get(key), path + "." + key)
        c.sources(row, path)
    constraints = c.rows(blocks["constraints"].get("items"), "mandate.constraints.items", True)
    c.unique(constraints, "constraint_id", "mandate.constraints.items")
    none = blocks["constraints"].get("none_identified")
    if not isinstance(none, bool):
        c.gap("mandate.constraints.none_identified", "Explicit none_identified boolean is required")
    elif bool(constraints) == none:
        c.gap(
            "mandate.constraints",
            "Constraint list and none_identified declaration conflict",
            "constraint-declaration-conflict",
        )
    for i, row in enumerate(constraints):
        path = f"mandate.constraints.items[{i}]"
        c.text(row.get("description"), path + ".description")
        c.sources(row, path)
    allocation = c.rows(mandate.get("allocation"), "mandate.allocation")
    c.unique(allocation, "asset_class", "mandate.allocation")
    normalized = set()
    for i, row in enumerate(allocation):
        path = f"mandate.allocation[{i}]"
        c.text(row.get("benchmark"), path + ".benchmark")
        c.sources(row, path)
        for key in ["target_pct", "min_pct", "max_pct"]:
            c.number(row.get(key), path + "." + key, 0, 100)
        if isinstance(row.get("asset_class"), str):
            name = row["asset_class"].strip().casefold()
            if name in normalized:
                c.errors.append("Repeated asset class after case normalization")
            normalized.add(name)
    method = c.choice(
        blocks["rebalancing"].get("method"), "mandate.rebalancing.method", {"calendar", "threshold", "hybrid"}
    )
    if method in {"threshold", "hybrid"}:
        c.number(
            blocks["rebalancing"].get("threshold_percentage_points"),
            "mandate.rebalancing.threshold_percentage_points",
            0.01,
            100,
        )
    c.strings(blocks["monitoring"].get("review_triggers"), "mandate.monitoring.review_triggers")
    approvals = c.rows(mandate.get("approvals"), "mandate.approvals")
    roles = c.unique(approvals, "role", "mandate.approvals")
    if roles != {"advisor", "supervisor", "client"}:
        c.gap(
            "mandate.approvals", "Supply advisor, supervisor and client approval-role assignments", "approval-role-gap"
        )
    for i, row in enumerate(approvals):
        path = f"mandate.approvals[{i}]"
        c.text(row.get("party_id"), path + ".party_id")
        c.sources(row, path)
        if (
            not isinstance(row.get("party_id"), str)
            or not isinstance(row.get("role"), str)
            or (row.get("party_id"), row.get("role")) not in party_roles
        ):
            c.gap(
                path + ".party_id",
                "Approval party and role must match a supplied governance assignment",
                "approval-party-gap",
            )
        if "status" in row and row["status"] != "pending":
            c.errors.append(path + " cannot grant approval in a draft request")
    if c.errors:
        return c.errors, c.findings, {}
    checks = {"status": "not-evaluable", "target_sum": None, "within_bands": None}
    if c.ready("mandate.allocation") and allocation:
        total = round(sum(row["target_pct"] for row in allocation), 8)
        bands = all(row["min_pct"] <= row["target_pct"] <= row["max_pct"] for row in allocation)
        checks = {
            "status": "consistent" if abs(total - 100) <= 0.000001 and bands else "inconsistent",
            "target_sum": total,
            "within_bands": bands,
        }
        if checks["status"] == "inconsistent":
            c.gap(
                "mandate.allocation",
                "Targets must total 100% (tolerance 0.000001 percentage points) and remain within supplied bands",
                "allocation-inconsistent",
            )
    draft_approvals = [{**row, "status": "pending", "effective_date": None} for row in approvals]
    sections = []
    for key, title in SECTIONS:
        content = draft_approvals if key == "approvals" else mandate.get(key)
        sections.append(
            {
                "key": key,
                "title": title,
                "state": "documented-for-review" if c.ready("mandate." + key) and content is not None else "needs-data",
                "content": content,
                "source_ids": all_sources(content),
            }
        )
    markdown = f"# Draft Investment Policy Statement — {doc.get('ips_id', 'unknown')}\n\nHuman review required. This draft has no effective date and conveys no approval.\n"
    for section in sections:
        markdown += (
            f"\n## {section['title']}\n\nEvidence state: {section['state']}\n\n" + describe(section["content"]) + "\n"
        )
    markdown += "\n## Upstream evidence issues\n\n" + describe(doc.get("upstream_issues")) + "\n"
    return (
        [],
        c.findings,
        {
            "ips_id": doc.get("ips_id"),
            "revision": doc.get("revision"),
            "supersedes_artifact_id": doc.get("supersedes_artifact_id"),
            "template": template,
            "draft_status": "draft",
            "effective_date": None,
            "sections": sections,
            "allocation_checks": checks,
            "approvals": draft_approvals,
            "draft_markdown": markdown,
            "standing_note": "Draft mandate only. Human review of the recommendation, authority and applicability remains required. No allocation, signature, trade or delivery is approved by this artifact.",
        },
    )


def compute(doc):
    errors, findings, result = inspect(doc)
    if errors:
        raise ValueError("; ".join(errors))
    result["upstream_issues"] = doc.get("upstream_issues")
    out = make_output(SKILL, doc, result, findings)
    out["input_snapshot"] = doc
    return out


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/request_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        print(json.dumps(compute(json.loads(path.read_text() if path else sys.stdin.read())), indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        print("ERROR", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
