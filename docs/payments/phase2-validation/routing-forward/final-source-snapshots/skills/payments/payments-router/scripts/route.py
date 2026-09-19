#!/usr/bin/env python3
"""Explicit-intent routing. No NLP classification, live tools, or authorization."""

import json
import sys
from pathlib import Path
from payment_contract import stable_hash, VERSION

REGISTRY = Path(__file__).resolve().parents[1] / "references/routes.json"


def route(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    registry = json.loads(REGISTRY.read_text())
    intent = request.get("intent")
    row = registry["intents"].get(intent)
    output = {
        "contract_version": VERSION,
        "request": request,
        "request_hash": stable_hash(request),
        "intent": intent,
        "status": "needs-clarification",
        "lead_skill": None,
        "supporting_skills": [],
        "planned_capability": None,
        "missing_context": [],
        "authority_granted": False,
        "target_validation": "required",
        "limitations": [],
        "registry_version": registry["version"],
    }
    if request.get("requested_action", "analyze") not in {"analyze", "draft"}:
        output.update(status="action-unavailable", limitations=["No action-taking runtime is implemented."])
        return output
    if not row:
        output["missing_context"] = ["supported explicit intent"]
        return output
    if row.get("requires_role") and request.get("participant") not in row["requires_role"]:
        output["missing_context"] = ["participant: " + ", ".join(row["requires_role"])]
        return output
    if row.get("planned"):
        output.update(status="capability-gap", planned_capability=row["planned"], limitations=[row["limitation"]])
        return output
    target = row.get("role_targets", {}).get(request.get("participant"), row["target"])
    output["missing_context"] = [key for key in row.get("required_context", []) if not request.get(key)]
    available = request.get("available_skills")
    if available is not None:
        if not isinstance(available, list) or any(not isinstance(x, str) for x in available):
            raise ValueError("available_skills must be a list of installed skill names")
        if target not in available:
            output.update(
                status="target-unavailable",
                limitations=["Required target is absent from supplied deployment inventory."],
            )
            return output
    output.update(status="routed", lead_skill=target, limitations=row.get("limitations", []))
    output["supporting_skills"] = [name for name in row.get("support", []) if name != target and (available is None or name in available)]
    if row.get("mode"):
        output["target_mode"] = row["mode"]
    output["required_inputs"] = row.get("required_inputs", [])
    return output


def validate(output):
    if not isinstance(output, dict) or not isinstance(output.get("request"), dict):
        return ["route must retain its request"]
    try:
        expected = route(output["request"])
    except (ValueError, TypeError, KeyError) as exc:
        return [str(exc)]
    return (
        [] if expected == output else ["route differs from request and current registry; routing grants no authority"]
    )


def main(argv):
    try:
        checking = bool(argv and argv[0] == "--validate")
        path = argv[1] if checking else argv[0]
        doc = json.loads(Path(path).read_text())
        if checking:
            errors = validate(doc)
            print(f"route validation: {len(errors)} error(s)")
            for error in errors:
                print("ERROR", error)
            return bool(errors)
        print(json.dumps(route(doc), indent=2))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
        print("ERROR", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
