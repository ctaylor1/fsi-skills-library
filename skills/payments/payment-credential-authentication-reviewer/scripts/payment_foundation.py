"""Portable Phase 2 analysis envelope. Lineage validation does not confer authority.

Each package supplies domain.validate(data) and domain.analyze(request). The latter
returns result, findings and handoffs. Bundled by sync_payment_foundation.py.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
import sys

from payment_contract import money, stable_hash

SCHEMA_VERSION = "1.0"
SUPPORTED_JURISDICTIONS = {"US", "EA", "UK"}
LIMITATIONS = [
    "Offline analysis of supplied evidence; source identity and truth are not authenticated.",
    "Draft decision support only; no approval, execution, filing, posting or binding customer commitment.",
    "Regional profiles are bounded source summaries; institution and national applicability require specialist review.",
]
FORBIDDEN_KEYS = {"pan", "fullpan", "cvv", "cvc", "pin", "pinblock", "trackdata", "fulltrackdata", "password", "apikey", "secretkey", "accesstoken"}


def _secret_fields(value, path="request"):
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            if re.sub(r"[_ -]", "", str(key).lower()) in FORBIDDEN_KEYS:
                errors.append(path + "." + str(key) + ": raw credential/card-authentication fields are prohibited; use opaque references")
            errors.extend(_secret_fields(child, path + "." + str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_secret_fields(child, f"{path}[{index}]"))
    return errors


def load_resource(name):
    local = Path(__file__).resolve().parents[1] / "references" / name
    canonical = Path(__file__).resolve().parent / name
    return json.loads((local if local.exists() else canonical).read_text())


def load_rail_profile(profile_id):
    return deepcopy(load_resource("rail-profiles.json")["profiles"].get(profile_id))


def finding(code, message, source_ids=None, severity="gap"):
    return {"code": code, "message": message, "source_ids": source_ids or [], "severity": severity}


def dec(value):
    return money(value)


def _source_links(value, known, path="data"):
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "source_ids":
                if not isinstance(child, list) or any(not isinstance(s, str) or s not in known for s in child):
                    errors.append(f"{path}.source_ids must reference registered source IDs")
            else:
                errors.extend(_source_links(child, known, path + "." + str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_source_links(child, known, f"{path}[{index}]"))
    return errors


def validate_request(doc, domain):
    if not isinstance(doc, dict):
        return ["request must be an object"]
    errors = _secret_fields(doc)
    if doc.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 1.0")
    for key in ("request_id", "as_of", "jurisdiction", "participant"):
        if not isinstance(doc.get(key), str) or not doc[key].strip():
            errors.append(key + " required")
    try:
        current = date.fromisoformat(doc["as_of"])
    except (KeyError, TypeError, ValueError):
        current = None
        errors.append("as_of must be an ISO date")
    if doc.get("requested_action", "analyze") not in {"analyze", "draft"}:
        errors.append("requested_action permits analysis or drafting only")
    sources = doc.get("sources")
    known = set()
    if not isinstance(sources, list):
        errors.append("sources must be a list; an empty list represents missing evidence")
        sources = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        sid = source.get("source_id")
        if not isinstance(sid, str) or not sid.strip():
            errors.append("source_id required")
        elif sid in known:
            errors.append("duplicate source_id: " + sid)
        else:
            known.add(sid)
        if not isinstance(source.get("reference"), str) or not source["reference"].strip():
            errors.append("source reference required")
        try:
            observed = date.fromisoformat(source["as_of"])
            if current is not None and observed > current:
                errors.append("source date is after request as_of")
            if source.get("review_due"):
                date.fromisoformat(source["review_due"])
        except (KeyError, TypeError, ValueError):
            errors.append("source requires valid as_of and optional review_due dates")
    upstream = doc.get("upstream_issues", [])
    if not isinstance(upstream, list):
        errors.append("upstream_issues must be a list")
    else:
        for issue in upstream:
            if not isinstance(issue, dict) or not issue.get("code") or not issue.get("message"):
                errors.append("upstream issue requires code and message")
    data = doc.get("data")
    if not isinstance(data, dict):
        errors.append("data must be an object")
    else:
        errors.extend(_source_links(data, known))
        try:
            errors.extend(domain.validate(data))
        except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
            errors.append("domain input structure: " + str(exc))
    errors.extend(_source_links(upstream, known, "upstream_issues"))
    try:
        stable_hash(doc)
    except (TypeError, ValueError):
        errors.append("request must contain finite JSON values")
    return errors


def build(doc, domain):
    errors = validate_request(doc, domain)
    if errors:
        raise ValueError("; ".join(errors))
    # An installed optional module may declare its own bounded regional scope.
    # Request data never enables regions for a core workflow implicitly.
    supported = getattr(domain, "SUPPORTED_JURISDICTIONS", SUPPORTED_JURISDICTIONS)
    unsupported = doc["jurisdiction"] not in supported
    if unsupported:
        analysis = {"result": {}, "findings": [finding("unsupported-jurisdiction", "No operational profile is supplied for " + doc["jurisdiction"])], "handoffs": []}
    else:
        analysis = domain.analyze(deepcopy(doc))
    if not isinstance(analysis, dict) or not isinstance(analysis.get("result"), dict):
        raise ValueError("domain analysis must return a result object")
    findings = deepcopy(analysis.get("findings", []))
    for issue in doc.get("upstream_issues", []):
        findings.append(finding("upstream:" + issue["code"], issue["message"], issue.get("source_ids", [])))
    if not doc["sources"]:
        findings.append(finding("missing-sources", "Register source evidence before relying on this analysis."))
    for source in doc["sources"]:
        if source.get("review_due") and doc["as_of"] > source["review_due"]:
            findings.append(finding("stale-source", "Source review is overdue: " + source["source_id"], [source["source_id"]]))
    for item in findings:
        if not isinstance(item, dict) or not item.get("code") or not item.get("message") or item.get("severity") not in {"gap", "warning", "info"}:
            raise ValueError("findings require code, message and gap/warning/info severity")
    known = {s["source_id"] for s in doc["sources"]}
    link_errors = _source_links(analysis, known, "analysis")
    if link_errors:
        raise ValueError("; ".join(link_errors))
    handoffs = deepcopy(analysis.get("handoffs", []))
    if not isinstance(handoffs, list):
        raise ValueError("handoffs must be a list")
    for index, handoff in enumerate(handoffs):
        if not isinstance(handoff, dict) or not handoff.get("target_skill") or not handoff.get("reason") or not isinstance(handoff.get("required_inputs"), list):
            raise ValueError("handoffs require target_skill, reason and required_inputs")
        handoff.update({"handoff_id": stable_hash({"request_id": doc["request_id"], "input_hash": stable_hash(doc), "target": handoff["target_skill"], "index": index}),
                        "contract_version": "1.0.0", "source_skill": domain.SKILL,
                        "case_id": doc["request_id"], "lead_owner": doc["participant"],
                        "requested_output": handoff["reason"], "source_refs": [s["reference"] for s in doc["sources"]],
                        "unresolved_issues": [deepcopy(f) for f in findings if f["severity"] == "gap"],
                        "action_mode": "draft-only", "authority_granted": False,
                        "target_validation": "required"})
        handoff.setdefault("target_input", {})
    return {
        "schema_version": SCHEMA_VERSION, "skill": domain.SKILL,
        "request_id": doc["request_id"], "as_of": doc["as_of"],
        "jurisdiction": doc["jurisdiction"], "participant": doc["participant"],
        "status": "unsupported" if unsupported else "needs-evidence" if any(f["severity"] == "gap" for f in findings) else "draft",
        "action_mode": "draft-only", "authority_granted": False, "action_taken": False,
        "source_snapshot": deepcopy(doc), "input_hash": stable_hash(doc),
        "findings": findings, "result": analysis["result"], "handoffs": handoffs,
        "unresolved_issues": deepcopy(doc.get("upstream_issues", [])),
        "limitations": LIMITATIONS + list(analysis.get("limitations", [])),
    }


def validate_output(output, domain, external_input=None):
    if not isinstance(output, dict) or not isinstance(output.get("source_snapshot"), dict):
        return ["source_snapshot required"]
    source = output["source_snapshot"]
    if external_input is not None and source != external_input:
        return ["source snapshot differs from separately supplied input"]
    try:
        expected = build(source, domain)
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
        return ["invalid retained input: " + str(exc)]
    return [] if output == expected else ["output does not match source-bound recomputation"]


def main(domain, mode):
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--input")
    args = parser.parse_args()
    try:
        doc = json.loads(Path(args.path).read_text())
        if mode == "input":
            errors = validate_request(doc, domain)
            result = {"valid": not errors, "errors": errors}
        elif mode == "output":
            original = json.loads(Path(args.input).read_text()) if args.input else None
            errors = validate_output(doc, domain, original)
            result = {"valid": not errors, "errors": errors}
        elif mode == "calculate":
            result = build(doc, domain)
            errors = []
        else:
            raise ValueError("unknown CLI mode")
        print(json.dumps(result, indent=2, allow_nan=False))
        return int(bool(errors))
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError, OSError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}))
        return 1


if __name__ == "__main__":
    sys.exit("Import this helper from a skill's native CLI.")
