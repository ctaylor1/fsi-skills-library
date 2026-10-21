#!/usr/bin/env python3
"""Independent synthetic expectations; runs without writing result files."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from calculate_or_transform import compute, validate as validate_input
from validate_output import validate as validate_output


def check_output(request, result):
    errors, _ = validate_output(result, request)
    assert not errors, errors
    assert result["action_taken"] is False
    assert result["authority_granted"] is False
    assert result["human_review_required"] is True
    assert result["delivery_status"] == "not-delivered"
    assert result["source_truth"] == "unverified"
    assert result["unresolved_issues"] == request.get("unresolved_issues", [])
    for plan in result["plans"]:
        assert plan["launch_performed"] is False
        references = ([plan["primary"]] if plan["primary"] else []) + plan["supporting"]
        for ref in references:
            expected = "unknown" if "available_skills" not in request else (
                "installed" if ref["name"] in request["available_skills"] else "not_installed")
            assert ref["installation_status"] == expected
            assert ref["installation_evidence"] == (
                "not-supplied" if "available_skills" not in request else "caller-declared")
            assert ref["execution_authorized"] is False


def main():
    matrix = json.loads((ROOT / "evals/files/route_cases.json").read_text())
    assert len(matrix["cases"]) == 59
    assert len({row["intent"] for row in matrix["cases"]}) == 59
    for row in matrix["cases"]:
        # Expectations are hand-declared in the fixture, never read from routes.json.
        request = dict(request_id="matrix-" + row["intent"], as_of="2026-09-20",
                       intents=[row["intent"]], subject={"type": row["subject_type"], "id": "SYNTHETIC-001"},
                       requested_action="review", unresolved_issues=["SYNTHETIC-SOURCE-GAP-01"])
        for inventory in (None, [], [row["primary"]] if row["primary"] else []):
            case = copy.deepcopy(request)
            if inventory is not None:
                case["available_skills"] = inventory
            output = compute(case)
            check_output(case, output)
            assert len(output["plans"]) == 1
            plan = output["plans"][0]
            assert plan["status"] == row["status"], (row["intent"], plan)
            assert plan["subject_compatible"] is True
            if "native_extension" in row: assert plan["primary"]["native_extension"] == row["native_extension"]
            if "native_mode" in row: assert plan["primary"]["native_mode"] == row["native_mode"]
            assert (plan["primary"]["name"] if plan["primary"] else None) == row["primary"]
            assert {v["name"] for v in plan["supporting"]} == set(row["supporting"])

        for subject_type, action, expected in (
            ("unrecognized-subject", "review", "needs_scope_clarification"),
            (row["subject_type"], "execute", "execution_not_supported"),
            ("unrecognized-subject", "execute", "execution_not_supported"),
        ):
            case = copy.deepcopy(request)
            case["subject"]["type"] = subject_type
            case["requested_action"] = action
            output = compute(case)
            check_output(case, output)
            assert output["plans"][0]["status"] == expected

    base = json.loads((ROOT / "evals/files/bounded_input.json").read_text())
    original = compute(base)
    # Independent output attacks: result validation must use the retained original.
    for key, value in (("action_taken", True), ("source_truth", "authenticated"),
                       ("unresolved_issues", []), ("unreviewed_narrative", "Approved investment")):
        altered = copy.deepcopy(original)
        altered[key] = value
        assert validate_output(altered, base)[0], key
    altered = copy.deepcopy(original)
    altered["plans"][0]["status"] = "approved"
    assert validate_output(altered, base)[0]
    assert validate_output(original)[0], "detached original is required"
    changed_request = copy.deepcopy(base)
    changed_request["unresolved_issues"].append("new unresolved fact")
    changed_output = compute(changed_request)
    assert changed_output["input_hash"] != original["input_hash"]
    assert changed_output["route_id"] != original["route_id"]
    assert validate_output(original, changed_request)[0]

    duplicate = copy.deepcopy(base)
    duplicate["intents"] = ["mandate_review", "portfolio_underperformance", "mandate_review"]
    result = compute(duplicate)
    assert [p["intent"] for p in result["plans"]] == ["mandate_review", "portfolio_underperformance"]
    check_output(duplicate, result)

    # A mode's retired package name cannot claim the canonical package is installed.
    mode_request = dict(request_id="mode-inventory", as_of="2026-09-20",
                        intents=["investment_data_platform"],
                        subject={"type": "platform", "id": "PLATFORM-SYNTHETIC"},
                        available_skills=["investment-vendor-feed-reconciler"])
    result = compute(mode_request)
    quality = next(p for p in result["plans"][0]["supporting"]
                   if p["name"] == "investment-data-quality-reviewer")
    assert quality["installation_status"] == "not_installed"
    mode_request["available_skills"] = ["investment-data-quality-reviewer"]
    result = compute(mode_request)
    quality = next(p for p in result["plans"][0]["supporting"]
                   if p["name"] == "investment-data-quality-reviewer")
    assert quality["installation_status"] == "installed"
    assert result["plans"][0]["status"] == "bounded_route"

    for field, value in (("as_of", "2026-02-30"), ("as_of", "2026-09-20T00:00:00Z"),
                         ("intents", ["approve_and_execute"]), ("intents", []),
                         ("available_skills", "all"), ("available_skills", [None]),
                         ("requested_action", "approve"), ("unresolved_issues", [""]),
                         ("subject", {"type": "portfolio", "id": ""}),
                         ("unexpected_numeric", float("nan"))):
        invalid = copy.deepcopy(base)
        invalid[field] = value
        assert validate_input(invalid)[0], (field, value)
        try:
            compute(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError((field, value))
    print("PASS: 59 declared intents; independent primary/support/status expectations; 354 route variants; source, scope, installation, execution and invalid-input controls")


if __name__ == "__main__":
    main()
