#!/usr/bin/env python3
"""Build a fact-find from supplied evidence without inference or external actions."""
from __future__ import annotations
import copy
import json
import sys
from pathlib import Path
from wealth_contract import make_output
from validate_input import validate, findings

SKILL = "wealth-client-discovery-assistant"

def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    gaps = findings(doc)
    result = {key: copy.deepcopy(doc[key]) for key in ("household", "members", "facts", "goals", "engagement_details", "coverage")}
    result["input_snapshot"] = copy.deepcopy(doc)
    result["counts"] = {key: len(doc[key]) for key in ("members", "facts", "goals")}
    result["scope_note"] = "Documented intake only. Client-reported facts remain client-reported; no identity verification, KYC conclusion, risk determination, recommendation, or account action."
    result["handoffs"] = [
        {"to": "wealth-onboarding-packager", "purpose": "Confirm account/engagement readiness separately; this fact-find grants no permission."},
        {"to": "investment-recommendation-evidence-reviewer", "purpose": "Review recommendation evidence only when a separate recommendation workflow is requested."},
    ]
    return make_output(SKILL, doc, result, gaps)

def main(argv):
    path = Path(__file__).resolve().parents[1] / "evals/files/discovery_request.json" if "--selftest" in argv else None
    doc = json.loads(path.read_text() if path else Path(argv[0]).read_text() if argv else sys.stdin.read())
    try:
        output = build(doc)
    except ValueError as exc:
        print(json.dumps({"status": "needs-data", "errors": [str(exc)], "action_taken": False}))
        return 1
    print(json.dumps(output, indent=2, allow_nan=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
