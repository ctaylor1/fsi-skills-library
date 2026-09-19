#!/usr/bin/env python3
"""Check Phase 1 route availability, migration metadata and package integrity.

This validates registry/catalog/package relationships, not semantic suitability or
runtime authorization. Native target validation remains mandatory at handoff.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    errors = []
    catalog = json.loads((ROOT / "catalog/skills-catalog.json").read_text())["skills"]
    names = {row["name"] for row in catalog}
    packages = {p.parent.name: p.parent for p in (ROOT / "skills").glob("*/*/SKILL.md")}
    registry = json.loads((ROOT / "skills/payments/payments-router/references/routes.json").read_text())
    migrations = [json.loads(path.read_text()) for path in sorted((ROOT / "catalog").glob("payments-phase*-migrations.json"))]
    for intent, row in registry["intents"].items():
        if row.get("planned"):
            if row.get("target"):
                errors.append(f"{intent}: planned capability also has an executable route")
            continue
        for target in [row["target"]] + row.get("support", []) + list(row.get("role_targets", {}).values()):
            if target not in names or target not in packages:
                errors.append(f"{intent}: unavailable target {target}")
    aliases = {name: value for migration in migrations for name, value in migration["aliases"].items()}
    moves = {name: value for migration in migrations for name, value in migration.get("moves", {}).items()}
    for old, change in aliases.items():
        if old in names or old in packages:
            errors.append(f"retired alias still active: {old}")
        for target in [change["target"]] + list(change.get("participant_routes", {}).values()):
            if target not in names or target not in packages:
                errors.append(f"alias {old}: missing target {target}")
    for name, move in moves.items():
        expected = ROOT / "skills" / move["to"] / name
        if packages.get(name) != expected:
            errors.append(f"{name}: incorrect physical domain")
        if (ROOT / "skills" / move["from"] / name).exists():
            errors.append(f"{name}: old domain path remains")
    if len(names) != len(catalog):
        errors.append("catalog contains duplicate names")
    for name, package in packages.items():
        if package.parent.name == "payments" or name == "pci-dss-evidence-assistant":
            if name not in names:
                errors.append(f"package absent from catalog: {name}")
            if not (package / "references/payment-contract.md").exists():
                errors.append(f"package contract missing: {name}")
    return errors


if __name__ == "__main__":
    findings = check()
    for finding in findings:
        print("ERROR", finding)
    print(f"Payment routes/migrations: {len(findings)} error(s)")
    raise SystemExit(bool(findings))
