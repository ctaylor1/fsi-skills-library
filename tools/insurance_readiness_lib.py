"""Offline Insurance evidence inventory; never an approval or deployment engine."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path, PurePosixPath
import re
import stat

SCHEMA = "insurance-readiness/1.0"
GATES = (
    "specification",
    "scope-routing",
    "sources",
    "tools",
    "safety-compliance",
    "quality",
    "evaluations",
    "human-acceptance",
    "operations",
)
SCOPE_FIELDS = ("institution", "environment", "market", "program", "product", "jurisdiction", "method")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def stable_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def known(value):
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().lower() not in {"unknown", "n/a", "none", "null", "pending", "not supplied"}
    )


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    return json.loads(
        Path(path).read_text(),
        object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON value: " + value)),
    )


def safe_file(root, relative):
    """Only explicit regular files below a supplied local evidence/package root."""
    if not isinstance(relative, str) or "\\" in relative:
        raise ValueError("file path must be a relative POSIX path")
    name = PurePosixPath(relative)
    if name.is_absolute() or not name.parts or any(p in {".", ".."} for p in relative.split("/")):
        raise ValueError("file path cannot be absolute, empty or traverse directories")
    path = Path(root)
    for part in name.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symbolic links are not evidence/package files")
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("file is missing or not a regular file: " + relative)
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("file escapes supplied root")
    return path


def package_snapshot(package):
    package = Path(package)
    if package.is_symlink() or not package.is_dir():
        raise ValueError("package must be a real directory")
    files = {}
    for path in sorted(package.rglob("*")):
        relative = path.relative_to(package)
        if path.is_symlink():
            raise ValueError("package contains symbolic link: " + str(relative))
        if path.is_dir():
            continue
        if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("package contains special file: " + str(relative))
        if "__pycache__" in relative.parts or path.suffix == ".pyc" or path.name == ".DS_Store":
            continue
        files[relative.as_posix()] = file_hash(path)
    if not files or "SKILL.md" not in files:
        raise ValueError("package has no SKILL.md")
    return {"content_sha256": stable_hash(files), "files": files}


def portfolio_snapshot(root):
    root = Path(root).resolve()
    catalog = load_json(root / "catalog/skills-catalog.json")["skills"]
    by_name = {}
    for row in catalog:
        if row["name"] in by_name:
            raise ValueError("duplicate catalog skill: " + row["name"])
        by_name[row["name"]] = row
    migration = load_json(root / "catalog/insurance-phase1-migrations.json")
    expected = (
        {v["target"] for v in migration["aliases"].values()}
        | set(migration["retained_with_revisions"])
        | {"insurance-router"}
    )
    controls = [
        "catalog/insurance-phase1-migrations.json",
        "docs/BUILD-STANDARDS.md",
        "docs/insurance/SOURCE-GOVERNANCE.md",
        "docs/insurance/acceptance/requirements.json",
        "tools/insurance_readiness_lib.py",
        "tools/check_insurance_readiness.py",
        "tools/run_insurance_portable.py",
    ]
    for phase in (2, 3, 4, 5):
        path = f"catalog/insurance-phase{phase}-capabilities.json"
        expected.update(load_json(root / path)["packages"])
        controls.append(path)
    actual = {p.parent.name for p in (root / "skills/insurance").glob("*/SKILL.md")}
    if actual != expected:
        raise ValueError("Insurance package inventory differs from approved phases")
    shared = load_json(root / "catalog/insurance-phase4-capabilities.json")["shared_packages"]
    paths = {name: "skills/insurance/" + name for name in sorted(expected)} | shared
    packages = []
    for name, relative in sorted(paths.items()):
        if name not in by_name:
            raise ValueError("package absent from catalog: " + name)
        safe_file(root, relative + "/SKILL.md")
        if Path(relative).name != name:
            raise ValueError("manifest package name/path mismatch")
        row = by_name[name]
        evaluations = load_json(safe_file(root, relative + "/evals/evals.json"))
        if not isinstance(evaluations, dict) or not isinstance(evaluations.get("evals"), list):
            raise ValueError("evaluation manifest requires an evals array")
        expected_checks = []
        seen_ids = set()
        for collection in ("evals", "planned_natural_language_evals"):
            cases = evaluations.get(collection, [])
            if not isinstance(cases, list):
                raise ValueError("evaluation collection must be an array")
            for case in cases:
                if not isinstance(case, dict) or not known(case.get("id")) or case["id"] in seen_ids:
                    raise ValueError("evaluations require unique known IDs and object records")
                seen_ids.add(case["id"])
                if "command" in case:
                    if collection != "evals" or not known(case["command"]) or type(case.get("expect_exit")) is not int:
                        raise ValueError("executable evaluation requires command and integer expected exit")
                    contains = case.get("expect_contains", [])
                    if not isinstance(contains, list) or any(not isinstance(x, str) for x in contains):
                        raise ValueError("expect_contains requires a string array")
                    expected_checks.append(
                        {
                            "id": case["id"],
                            "command": case["command"],
                            "expect_exit": case["expect_exit"],
                            "expect_contains": contains,
                        }
                    )
        if not expected_checks:
            raise ValueError("package requires at least one executable evaluation")
        packages.append(
            {
                "name": name,
                "path": relative,
                "category": row["category"],
                "version": row.get("version"),
                "risk_tier": row.get("risk_tier"),
                "primary_user": row.get("primary_user"),
                "catalog_row": row,
                "checks_manifest_sha256": stable_hash(evaluations),
                "expected_checks": expected_checks,
                **package_snapshot(root / relative),
            }
        )
    result = {
        "schema_version": SCHEMA,
        "insurance_packages": len(expected),
        "shared_packages": len(shared),
        "packages": packages,
        "control_files": {p: file_hash(safe_file(root, p)) for p in controls},
        "scope": "Current Insurance packages plus the four installed Phase 4 shared owners; no transitive installation or external source access",
    }
    result["snapshot_sha256"] = stable_hash(result)
    return result


def iso_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def assess_records(snapshot, packet, evidence_root, scope, as_of):
    """Validate supplied review records without authenticating people or approvals."""
    as_of = iso_day(as_of)
    if not isinstance(scope, dict) or set(scope) != set(SCOPE_FIELDS):
        raise ValueError("assessment scope must contain exactly " + ", ".join(SCOPE_FIELDS))
    if any(value is not None and not known(value) for value in scope.values()):
        raise ValueError("scope fields must be known text or explicit null")
    if (
        not isinstance(packet, dict)
        or set(packet) != {"schema_version", "records"}
        or packet.get("schema_version") != "insurance-review-records/1.0"
        or not isinstance(packet.get("records"), list)
    ):
        raise ValueError("review packet requires insurance-review-records/1.0 and records array")
    packages = {p["name"]: p for p in snapshot["packages"]}
    indexed = {}
    seen = set()
    assessed = []
    for record in packet["records"]:
        if not isinstance(record, dict):
            raise ValueError("review record must be an object")
        rid = record.get("record_id")
        name = record.get("package")
        gate = record.get("gate")
        if not known(rid) or rid in seen:
            raise ValueError("review record IDs must be unique known text")
        seen.add(rid)
        if not isinstance(name, str) or not isinstance(gate, str) or name not in packages or gate not in GATES:
            raise ValueError("unknown package or release gate in " + rid)
        indexed.setdefault((name, gate), []).append(rid)
        issues = []
        if set(record) != {
            "record_id",
            "package",
            "gate",
            "content_sha256",
            "scope",
            "reviewer",
            "reviewed_on",
            "effective_from",
            "expires_on",
            "decision",
            "rationale",
            "evidence_kind",
            "evidence",
            "unresolved_issues",
        }:
            issues.append("record-fields")
        if record.get("content_sha256") != packages[name]["content_sha256"]:
            issues.append("package-changed")
        if not all(known(v) for v in scope.values()):
            issues.append("assessment-scope-unknown")
        if (
            record.get("scope") != scope
            or not isinstance(record.get("scope"), dict)
            or not all(known(v) for v in record.get("scope", {}).values())
        ):
            issues.append("scope-mismatch")
        reviewer = record.get("reviewer")
        if (
            not isinstance(reviewer, dict)
            or set(reviewer) != {"name", "role", "authority_basis"}
            or not all(known(v) for v in reviewer.values())
        ):
            issues.append("reviewer-unresolved")
        try:
            reviewed, effective, expiry = [
                iso_day(record.get(k)) for k in ("reviewed_on", "effective_from", "expires_on")
            ]
            if not reviewed <= as_of or not effective <= as_of <= expiry or reviewed > expiry:
                issues.append("review-not-current")
        except ValueError:
            issues.append("review-date-invalid")
        decision = record.get("decision")
        if (
            not isinstance(decision, str)
            or decision not in {"accepted", "rejected", "needs-work", "not-applicable"}
            or not known(record.get("rationale"))
        ):
            issues.append("decision-unresolved")
        if record.get("evidence_kind") != "institutional":
            issues.append("non-institutional-evidence")
        unresolved = record.get("unresolved_issues")
        if not isinstance(unresolved, list) or any(not known(x) for x in unresolved):
            issues.append("issue-register-invalid")
        elif unresolved:
            issues.append("unresolved-issues")
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            issues.append("evidence-missing")
        else:
            seen_paths = set()
            for item in evidence:
                if (
                    not isinstance(item, dict)
                    or set(item) != {"path", "sha256", "locator"}
                    or not known(item.get("locator"))
                    or not isinstance(item.get("sha256"), str)
                    or not DIGEST.fullmatch(item["sha256"])
                ):
                    issues.append("evidence-reference-invalid")
                    continue
                if not isinstance(item.get("path"), str):
                    issues.append("evidence-reference-invalid")
                    continue
                if item["path"] in seen_paths:
                    issues.append("duplicate-evidence")
                    continue
                seen_paths.add(item["path"])
                try:
                    actual = file_hash(safe_file(evidence_root, item["path"]))
                    if actual != item["sha256"]:
                        issues.append("evidence-changed")
                except (ValueError, OSError):
                    issues.append("evidence-unavailable")
        assessed.append(
            {
                "record_id": rid,
                "package": name,
                "gate": gate,
                "decision": decision,
                "record_sha256": stable_hash(record),
                "issues": sorted(set(issues)),
                "status": "invalid-or-unresolved" if issues else "supplied-unverified",
                "reviewer_identity_authenticated": False,
                "professional_acceptance_established": False,
            }
        )
    # Never choose a latest record or silently discard a rejected/conflicting review.
    for row in assessed:
        if len(indexed[(row["package"], row["gate"])]) != 1:
            row["issues"].append("multiple-records-require-reconciliation")
            row["status"] = "invalid-or-unresolved"
    cells = []
    for name in sorted(packages):
        for gate in GATES:
            matching = [x for x in assessed if x["package"] == name and x["gate"] == gate]
            status = (
                "not-supplied"
                if not matching
                else "invalid-or-unresolved"
                if any(x["issues"] for x in matching)
                else "recorded-negative"
                if matching[0]["decision"] in {"rejected", "needs-work"}
                else "supplied-unverified"
            )
            cells.append(
                {"package": name, "gate": gate, "status": status, "record_ids": [x["record_id"] for x in matching]}
            )
    return {
        "records": assessed,
        "gates": cells,
        "supplied_packet_sha256": stable_hash(packet),
        "scope": scope,
        "as_of": as_of.isoformat(),
        "acceptance": "not-established",
        "source_authentication": "not-performed",
        "deployment_authorized": False,
        "action_taken": False,
        "supplied_review_packet": packet,
    }


def assess_portable(snapshot, report):
    """Match complete runtime observations; a supplied report is still unverified."""
    if report is None:
        return {"status": "not-supplied", "issues": []}
    issues = []
    if not isinstance(report, dict):
        return {"status": "invalid", "issues": ["report must be an object"]}
    if (
        report.get("schema_version") != "portable-insurance/1.0"
        or report.get("snapshot_sha256") != snapshot["snapshot_sha256"]
    ):
        issues.append("snapshot-or-schema-mismatch")
    expected = {p["name"]: p["content_sha256"] for p in snapshot["packages"]}
    package_by = {p["name"]: p for p in snapshot["packages"]}
    rows = report.get("packages", [])
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        issues.append("package-results-invalid")
        rows = []
    names = [r.get("name") for r in rows]
    if len(names) != len(set(str(n) for n in names)) or set(str(n) for n in names) != set(expected):
        issues.append("package-coverage-mismatch")
    for row in rows:
        package = package_by.get(row.get("name")) if isinstance(row.get("name"), str) else None
        if package is None or row.get("content_sha256") != package["content_sha256"]:
            issues.append("package-version-mismatch")
        if package and row.get("checks_manifest_sha256") != package.get("checks_manifest_sha256"):
            issues.append("check-manifest-mismatch")
        if row.get("software_checks_passed") is not True or row.get("errors") != []:
            issues.append("package-checks-not-passed")
        if package:
            pinned = {"content_sha256": package["content_sha256"], "files": package.get("files", {})}
            if any(row.get(key) != pinned for key in ("source_before", "source_after", "copy_before", "copy_after")):
                issues.append("package-integrity-mismatch")
        checks = row.get("checks")
        if (
            not isinstance(checks, list)
            or not checks
            or any(not isinstance(c, dict) or c.get("passed") is not True for c in checks)
        ):
            issues.append("checks-missing-or-failed")
        if package and isinstance(checks, list) and all(isinstance(c, dict) for c in checks):
            declared = {c["id"]: c for c in package.get("expected_checks", [])}
            ids = [c.get("id") for c in checks]
            if len(ids) != len(set(str(x) for x in ids)) or set(str(x) for x in ids) != set(declared):
                issues.append("command-coverage-mismatch")
            for check in checks:
                original = declared.get(check.get("id")) if isinstance(check.get("id"), str) else None
                if original:
                    if (
                        check.get("command") != original["command"]
                        or type(check.get("expected_exit")) is not int
                        or check.get("expected_exit") != original["expect_exit"]
                        or check.get("expect_contains") != original["expect_contains"]
                    ):
                        issues.append("command-contract-mismatch")
                    if (
                        check.get("executed") is not True
                        or check.get("timed_out") is not False
                        or type(check.get("actual_exit")) is not int
                        or check.get("actual_exit") != original["expect_exit"]
                        or check.get("error") is not None
                        or check.get("contains_checks")
                        != [{"value": value, "matched": True} for value in original["expect_contains"]]
                    ):
                        issues.append("command-observation-mismatch")
                    for location in ("source", "copy"):
                        for when in ("before", "after"):
                            if check.get(f"{location}_content_sha256_{when}") != package["content_sha256"]:
                                issues.append("command-integrity-mismatch")
    if report.get("errors") != [] or any(
        report.get(key) != snapshot["snapshot_sha256"]
        for key in ("source_snapshot_sha256_before", "source_snapshot_sha256_after")
    ):
        issues.append("portfolio-integrity-mismatch")
    if report.get("software_checks_passed") is not True:
        issues.append("software-checks-not-passed")
    if report.get("institution_acceptance") != "not-established" or report.get("action_taken") is not False:
        issues.append("unsupported-authority-claim")
    return {
        "status": "invalid-or-failed" if issues else "matching-supplied-software-report",
        "issues": sorted(set(issues)),
        "report_sha256": stable_hash(report),
        "source_authentication": "not-performed",
        "professional_acceptance_established": False,
    }
