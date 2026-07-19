#!/usr/bin/env python3
"""Deterministic input validation for third-party-risk-assessor.

Validates a vendor assessment file before dimension scoring. Fails closed on structural
problems; warns on data-quality / evidence-traceability gaps that limit which dimensions are
evaluable.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  vendor_id, vendor_name, as_of (YYYY-MM-DD), config_version, framework_version,
  criticality{supports_critical_operation,substitutability_days,annual_spend,source_ref},
  controls[{control_id,domain,status,last_tested,source_ref}],
  concentration{vendor_share_of_function,single_point_of_failure,source_ref},
  subcontractors[{name,country,critical,disclosed,source_ref}],
  data{classification,pii,records_count,source_ref},
  resilience{rto_hours,bcp_tested,last_bcp_test,sla_uptime,source_ref},
  financials{going_concern_flag,credit_rating,current_ratio,debt_to_equity,net_margin,source_ref},
  exit_plan{documented,tested,alternate_provider_identified,source_ref}, config{...}

Usage:
  python validate_input.py assessment.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise (prints a line ending "N error(s)").
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("vendor_id", "vendor_name", "as_of", "config_version")
CONTROL_STATUSES = {"effective", "partial", "ineffective", "missing"}
DATA_CLASSES = {"public", "internal", "confidential", "restricted"}
DIMENSION_BLOCKS = ("criticality", "controls", "concentration", "subcontractors",
                    "data", "resilience", "financials", "exit_plan")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict):
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    present_blocks = [b for b in DIMENSION_BLOCKS if doc.get(b) not in (None, "")]
    if not present_blocks:
        errors.append("no risk-dimension blocks present; at least one is required to assess")
        return errors, warnings
    for b in DIMENSION_BLOCKS:
        if doc.get(b) in (None, ""):
            warnings.append(f"missing '{b}' block — the corresponding dimension will be not_evaluable")

    # criticality
    crit = doc.get("criticality")
    if isinstance(crit, dict):
        if "supports_critical_operation" in crit and not isinstance(crit["supports_critical_operation"], bool):
            errors.append("criticality.supports_critical_operation must be boolean")
        if crit.get("substitutability_days") is not None and _num(crit.get("substitutability_days")) is None:
            errors.append("criticality.substitutability_days must be numeric")
        if not crit.get("source_ref"):
            warnings.append("criticality has no source_ref — evidence will not be traceable")
    elif crit is not None:
        errors.append("criticality must be an object")

    # controls
    controls = doc.get("controls")
    if controls is not None:
        if not isinstance(controls, list):
            errors.append("controls must be a list")
        else:
            seen = set()
            for i, c in enumerate(controls):
                tag = f"controls[{i}] ({c.get('control_id','?')})"
                for k in ("control_id", "domain", "status"):
                    if not c.get(k):
                        errors.append(f"{tag}: missing '{k}'")
                st = str(c.get("status", "")).lower()
                if st and st not in CONTROL_STATUSES:
                    errors.append(f"{tag}: status {c.get('status')!r} not in {sorted(CONTROL_STATUSES)}")
                cid = c.get("control_id")
                if cid in seen:
                    errors.append(f"{tag}: duplicate control_id")
                seen.add(cid)
                if not c.get("source_ref"):
                    warnings.append(f"{tag}: no source_ref — control evidence not traceable")
                if not c.get("last_tested") and st not in ("missing", ""):
                    warnings.append(f"{tag}: no last_tested date — control treated as stale/gap")

    # concentration
    conc = doc.get("concentration")
    if isinstance(conc, dict):
        sh = _num(conc.get("vendor_share_of_function")) if conc.get("vendor_share_of_function") is not None else None
        if conc.get("vendor_share_of_function") is not None and sh is None:
            errors.append("concentration.vendor_share_of_function must be numeric")
        elif sh is not None and not (0.0 <= sh <= 1.0):
            errors.append(f"concentration.vendor_share_of_function must be within [0,1], got {sh}")
    elif conc is not None:
        errors.append("concentration must be an object")

    # subcontractors
    subs = doc.get("subcontractors")
    if subs is not None:
        if not isinstance(subs, list):
            errors.append("subcontractors must be a list")
        else:
            for i, s in enumerate(subs):
                if not s.get("name"):
                    errors.append(f"subcontractors[{i}]: missing 'name'")
                if not s.get("country"):
                    warnings.append(f"subcontractors[{i}]: no country — elevated-jurisdiction check not evaluable")
            crit_flag = bool((doc.get("criticality") or {}).get("supports_critical_operation"))
            if crit_flag and not subs:
                warnings.append("vendor supports a critical operation but no subcontractors are disclosed — confirm fourth-party inventory")

    # data
    data = doc.get("data")
    if isinstance(data, dict):
        cls = str(data.get("classification", "")).lower()
        if cls and cls not in DATA_CLASSES:
            errors.append(f"data.classification {data.get('classification')!r} not in {sorted(DATA_CLASSES)}")
        if data.get("pii") is not None and not isinstance(data["pii"], bool):
            errors.append("data.pii must be boolean")
        if data.get("records_count") is not None and _num(data.get("records_count")) is None:
            errors.append("data.records_count must be numeric")
    elif data is not None:
        errors.append("data must be an object")

    # resilience
    res = doc.get("resilience")
    if isinstance(res, dict):
        for k in ("rto_hours", "rpo_hours", "sla_uptime"):
            if res.get(k) is not None and _num(res.get(k)) is None:
                errors.append(f"resilience.{k} must be numeric")
        if res.get("bcp_tested") is not None and not isinstance(res["bcp_tested"], bool):
            errors.append("resilience.bcp_tested must be boolean")
    elif res is not None:
        errors.append("resilience must be an object")

    # financials
    fin = doc.get("financials")
    if isinstance(fin, dict):
        for k in ("current_ratio", "debt_to_equity", "net_margin"):
            if fin.get(k) is not None and _num(fin.get(k)) is None:
                errors.append(f"financials.{k} must be numeric")
        if fin.get("going_concern_flag") is not None and not isinstance(fin["going_concern_flag"], bool):
            errors.append("financials.going_concern_flag must be boolean")
    elif fin is not None:
        errors.append("financials must be an object")

    # exit_plan
    exitp = doc.get("exit_plan")
    if isinstance(exitp, dict):
        for k in ("documented", "tested", "alternate_provider_identified"):
            if exitp.get(k) is not None and not isinstance(exitp[k], bool):
                errors.append(f"exit_plan.{k} must be boolean")
    elif exitp is not None:
        errors.append("exit_plan must be an object")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
