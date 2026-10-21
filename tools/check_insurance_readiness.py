#!/usr/bin/env python3
"""Create a new offline Insurance review dossier; never approve or deploy a skill."""

from __future__ import annotations
import argparse
from collections import Counter
from datetime import date
import json
import html
from pathlib import Path
import sys

from insurance_readiness_lib import (
    SCOPE_FIELDS,
    assess_portable,
    assess_records,
    load_json,
    portfolio_snapshot,
    stable_hash,
)

ROOT = Path(__file__).resolve().parents[1]


def render_report(snapshot, assessment, software, selected):
    counts = Counter(row["status"] for row in assessment["gates"])
    lines = [
        "# Insurance acceptance evidence dossier",
        "",
        "Institutional acceptance: **not established**. Deployment authority: **none**.",
        "",
        f"Assessment date: {assessment['as_of']}. Selected packages: {len(selected)}.",
        f"Software evidence: `{software['status']}`. Package snapshot: `{snapshot['snapshot_sha256']}`.",
        "",
        "This is an inventory of local evidence and supplied review records. Matching hashes and",
        "complete records do not authenticate sources, reviewers, approval scope or professional decisions.",
        "",
        "## Review scope",
        "",
        "| Field | Supplied value |",
        "| --- | --- |",
    ]
    for key, value in assessment["scope"].items():
        safe = html.escape(str(value)).replace("|", "\\|").replace("\n", " ") if value is not None else "Not supplied"
        lines.append(f"| {key} | {safe} |")
    lines += ["", "## Gate evidence", "", "| State | Gate records |", "| --- | --- |"]
    lines += [f"| {state} | {count} |" for state, count in sorted(counts.items())]
    lines += [
        "",
        "| Package | Gates missing | Records unresolved | Supplied but unverified | Negative reviews |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in selected:
        c = Counter(row["status"] for row in assessment["gates"] if row["package"] == name)
        lines.append(
            f"| {name} | {c['not-supplied']} | {c['invalid-or-unresolved']} | {c['supplied-unverified']} | {c['recorded-negative']} |"
        )

    def literal(value):
        return html.escape(str(value)).replace("|", "\\|").replace("\n", " ")

    if assessment["records"]:
        lines += [
            "",
            "## Supplied review records",
            "",
            "These are supplied assertions. The tool has not authenticated the reviewer or evidence.",
            "",
        ]
        originals = {r["record_id"]: r for r in assessment["supplied_review_packet"]["records"]}
        for row in assessment["records"]:
            source = originals[row["record_id"]]
            reviewer = source.get("reviewer")
            reviewer = reviewer if isinstance(reviewer, dict) else {}
            lines += [
                "### " + literal(row["record_id"]),
                "",
                "Package: " + literal(row["package"]) + ". Gate: " + literal(row["gate"]) + ".",
                "Supplied decision: " + literal(row["decision"]) + ". Evidence state: " + literal(row["status"]) + ".",
                "Reviewer assertion: "
                + literal(reviewer.get("name"))
                + "; role: "
                + literal(reviewer.get("role"))
                + ".",
                "Review date: "
                + literal(source.get("reviewed_on"))
                + "; effective: "
                + literal(source.get("effective_from"))
                + "; expires: "
                + literal(source.get("expires_on"))
                + ".",
                "Rationale: " + literal(source.get("rationale")),
                "",
            ]
            if row["issues"]:
                lines += (
                    ["Unresolved checks:", ""]
                    + ["- " + literal(issue.replace("-", " ")) for issue in row["issues"]]
                    + [""]
                )
            if isinstance(source.get("unresolved_issues"), list) and source["unresolved_issues"]:
                lines += (
                    ["Supplied open issues:", ""]
                    + ["- " + literal(issue) for issue in source["unresolved_issues"]]
                    + [""]
                )
            if isinstance(source.get("evidence"), list):
                lines += ["Evidence references:", ""]
                for evidence in source["evidence"]:
                    if isinstance(evidence, dict):
                        lines += [
                            "- "
                            + literal(evidence.get("path"))
                            + " — "
                            + literal(evidence.get("locator"))
                            + "; supplied SHA-256: "
                            + literal(evidence.get("sha256"))
                        ]
                lines += [""]

    lines += [
        "",
        "## Follow-up",
        "",
        "Use the fixed nine release criteria and current package digest when collecting reviews.",
        "Supply actual institution/environment and market/program/product/jurisdiction/method scope.",
        "Have the existing accountable owners review source mapping, native handoffs, practitioner outputs,",
        "model behavior, privacy/access and operational recovery. Record failed and unresolved reviews.",
        "External source-workbook reconciliation is not established by this report or catalog regeneration.",
        "Synthetic cases and local package checks are supporting software evidence only.",
        "",
        "No external sources were contacted, no review was authenticated, and no release or action was authorized.",
    ]
    if software["issues"]:
        lines += ["", "## Software evidence issues", ""] + [f"- {issue}" for issue in software["issues"]]
    return "\n".join(lines) + "\n"


def build_dossier(root, scope, records, evidence_root, as_of, portable=None, packages=None):
    snapshot = portfolio_snapshot(root)
    names = {p["name"] for p in snapshot["packages"]}
    selected = sorted(set(packages or names))
    if not selected or any(name not in names for name in selected):
        raise ValueError("selected package is absent from the scoped portfolio")
    selection = {**snapshot, "packages": [p for p in snapshot["packages"] if p["name"] in selected]}
    assessment = assess_records(selection, records, evidence_root, scope, as_of)
    software = assess_portable(snapshot, portable)
    report = {
        "schema_version": "insurance-readiness-dossier/1.0",
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "selected_packages": selected,
        "assessment": assessment,
        "software_evidence": software,
        "portable_report": portable,
        "workbook_reconciliation": "not-assessed",
        "institution_acceptance": "not-established",
        "deployment_authorized": False,
        "action_taken": False,
    }
    report["dossier_sha256"] = stable_hash(report)
    if portfolio_snapshot(root)["snapshot_sha256"] != snapshot["snapshot_sha256"]:
        raise ValueError("source portfolio changed during dossier preparation")
    return snapshot, report, render_report(snapshot, assessment, software, selected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--scope", type=Path, help="Explicit scope JSON; omitted fields default to null only when no file is supplied"
    )
    parser.add_argument(
        "--records", type=Path, help="Supplied record packet; local evidence paths resolve beneath its directory"
    )
    parser.add_argument("--portable-report", type=Path)
    parser.add_argument(
        "--package", action="append", help="Optional subset of packages for one exact institutional review scope"
    )
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument(
        "--output-directory",
        required=True,
        type=Path,
        help="New output directory; existing evidence is never overwritten",
    )
    args = parser.parse_args(argv)
    try:
        if args.output_directory.exists():
            raise ValueError("output directory already exists; choose a new run directory")
        scope = load_json(args.scope) if args.scope else {key: None for key in SCOPE_FIELDS}
        packet = (
            load_json(args.records)
            if args.records
            else {"schema_version": "insurance-review-records/1.0", "records": []}
        )
        portable = load_json(args.portable_report) if args.portable_report else None
        snapshot, report, markdown = build_dossier(
            args.root,
            scope,
            packet,
            args.records.parent if args.records else args.root,
            args.as_of,
            portable,
            args.package,
        )
        args.output_directory.mkdir(parents=True, exist_ok=False)
        for name, value in [("snapshot.json", snapshot), ("readiness.json", report)]:
            path = args.output_directory / name
            path.write_text(json.dumps(value, indent=2) + "\n")
            if load_json(path) != value:
                raise ValueError("saved JSON readback mismatch")
        (args.output_directory / "report.md").write_text(markdown)
        if (args.output_directory / "report.md").read_text() != markdown:
            raise ValueError("saved report readback mismatch")
        print(
            f"Dossier saved for {len(report['selected_packages'])} packages; institutional acceptance not established."
        )
        print("Software evidence: " + report["software_evidence"]["status"])
        # Exit zero means the dossier was produced; open gates never become approvals.
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
