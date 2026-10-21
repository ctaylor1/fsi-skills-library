#!/usr/bin/env python3
"""Replay frozen independently reviewed Phase 5 inputs against current native packages."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/insurance/phase5-validation"


def main():
    cases = json.loads((EVIDENCE / "replay-cases.json").read_text())["cases"]
    packages = json.loads((ROOT / "catalog/insurance-phase5-capabilities.json").read_text())["all_native_packages"]
    destination = EVIDENCE / "final-replay"
    destination.mkdir(exist_ok=True)
    records = []
    for case in cases:
        package = ROOT / packages[case["skill"]]
        native = json.loads((EVIDENCE / case["input"]).read_text())
        expected = json.loads((EVIDENCE / case["reviewed_output"]).read_text())
        record = {"case_id": case["case_id"], "skill": case["skill"], "calls": [], "matches_reviewed_result": False}
        current = native
        for mode in ("validate_input", "calculate_or_transform", "validate_output"):
            proc = subprocess.run(
                [sys.executable, "-B", str(package / "scripts" / f"{mode}.py")],
                input=json.dumps(current),
                text=True,
                capture_output=True,
                cwd=package,
            )
            record["calls"].append(
                {
                    "script": mode,
                    "exit_code": proc.returncode,
                    "diagnostic": proc.stderr or (proc.stdout if mode != "calculate_or_transform" else ""),
                }
            )
            if proc.returncode:
                break
            if mode == "calculate_or_transform":
                current = json.loads(proc.stdout)
        if len(record["calls"]) == 3 and all(call["exit_code"] == 0 for call in record["calls"]):
            record["matches_reviewed_result"] = current == expected
            record["source_retained"] = current["source_document"] == native
            record["no_action"] = current["action_taken"] is False
            record["status"] = current["status"]
            (destination / (case["case_id"] + ".json")).write_text(json.dumps(current, indent=2) + "\n")
        records.append(record)
    passed = sum(r["matches_reviewed_result"] and r.get("source_retained") and r.get("no_action") for r in records)
    report = {
        "cases": len(records),
        "passed": passed,
        "native_calls": sum(len(r["calls"]) for r in records),
        "records": records,
        "claim": "Deterministic replay of bounded independently reviewed synthetic mappings; not a new agent trial or professional acceptance",
    }
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Insurance Phase 5 frozen replay: {passed}/{len(records)} cases; {report['native_calls']} native calls")
    return passed != len(records)


if __name__ == "__main__":
    raise SystemExit(main())
