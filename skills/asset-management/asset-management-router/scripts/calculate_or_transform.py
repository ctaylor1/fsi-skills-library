#!/usr/bin/env python3
"""Plan declared investment-management intents; never launch tools or workflows."""
from __future__ import annotations
import argparse
import json
from datetime import date
from pathlib import Path
from native_integrity import attach_source, canonical_hash

ROOT = Path(__file__).resolve().parents[1]
ROUTES = json.loads((ROOT / "references/routes.json").read_text())["routes"]
INDEX = {row["intent"]: row for row in ROUTES}


def validate(doc):
    if not isinstance(doc, dict): return ["request must be an object"], []
    errors = []
    try: canonical_hash(doc)
    except ValueError as exc: errors.append(str(exc))
    if not isinstance(doc.get("request_id"), str) or not doc["request_id"].strip():
        errors.append("request_id required")
    try:
        if date.fromisoformat(doc.get("as_of")).isoformat() != doc["as_of"]: raise ValueError()
    except (ValueError, TypeError): errors.append("as_of must be a real YYYY-MM-DD date")
    intents = doc.get("intents")
    if not isinstance(intents, list) or not intents or not all(isinstance(i, str) for i in intents):
        errors.append("intents must be a nonempty list of declared route identifiers")
    elif any(i not in INDEX for i in intents): errors.append("unknown intent; clarify the professional job before routing")
    subject = doc.get("subject")
    if not isinstance(subject, dict) or not all(isinstance(subject.get(k), str) and subject[k].strip() for k in ("type", "id")):
        errors.append("subject type and id required")
    if "available_skills" in doc and (not isinstance(doc["available_skills"], list) or not all(isinstance(s, str) and s for s in doc["available_skills"])):
        errors.append("available_skills must be a list of installed canonical names")
    if not isinstance(doc.get("requested_action", "review"), str) or doc.get("requested_action", "review") not in {"review", "analyze", "design", "prepare", "execute"}:
        errors.append("unsupported requested_action")
    if not isinstance(doc.get("unresolved_issues", []), list) or not all(isinstance(v,str) and v for v in doc.get("unresolved_issues", [])):
        errors.append("unresolved_issues must be nonempty strings")
    return errors, []


def compute(doc):
    errors, _ = validate(doc)
    if errors: raise ValueError("; ".join(errors))
    available = doc.get("available_skills")
    plans = []
    def availability(ref):
        if ref is None: return None
        item = dict(ref)
        item["installation_status"] = "unknown" if available is None else "installed" if item["name"] in available else "not_installed"
        item["installation_evidence"] = "not-supplied" if available is None else "caller-declared"
        item["execution_authorized"] = False
        return item
    for intent in dict.fromkeys(doc["intents"]):
        rule = INDEX[intent]
        compatible = doc["subject"]["type"] in rule["subject_types"]
        primary = availability(rule["primary"])
        status = "out_of_domain" if rule["out_of_domain"] else "planned_capability" if primary and primary["support_status"] == "planned" else "bounded_route"
        if not compatible: status = "needs_scope_clarification"
        if doc.get("requested_action") == "execute": status = "execution_not_supported"
        plans.append(dict(intent=intent,status=status,primary=primary,
            supporting=[availability(v) for v in rule["supporting"]],
            overlay_requirements=rule["overlay_requirements"],
            subject_compatible=compatible,launch_performed=False))
    output = dict(route_id="am-route-" + canonical_hash(doc)[:20],request_id=doc["request_id"],
                  as_of=doc["as_of"],subject=doc["subject"],plans=plans,
                  unresolved_issues=list(doc.get("unresolved_issues", [])),
                  action_taken=False,authority_granted=False,human_review_required=True,
                  delivery_status="not-delivered")
    return attach_source(output, doc)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("input")
    args=parser.parse_args()
    try: result=compute(json.loads(Path(args.input).read_text()))
    except (ValueError,TypeError,OSError) as exc: print(str(exc));return 1
    print(json.dumps(result,indent=2,allow_nan=False));return 0


if __name__ == "__main__": raise SystemExit(main())
