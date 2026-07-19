#!/usr/bin/env python3
"""Deterministic input validation for network-rules-change-tracker.

Validates a monitoring-run file before the change-tracking engine evaluates it. Fails closed
on structural problems; warns on data-quality gaps that limit which checks are evaluable or
that disable freshness / deduplication for this run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DD), config_version,
  feed_as_of, max_feed_staleness_days,                 # bulletin-feed freshness
  min_lead_days, readiness_bands{critical,high,medium},
  networks[],                                          # trusted publishers (authenticity)
  owners[],                                            # valid owner registry (ownership)
  open_alerts[{fingerprint}],                          # previously-open alerts, for dedup
  inventories{products[],processes[],controls[],contracts[],systems[]},
  bulletins[{bulletin_id, network, effective_date, source_ref, signature_verified, version,
             published_date, change_type,
             obligations[{obligation_id, summary, domains[], impacts{...}, owner,
                          required_lead_days, implementation{status,tracker_ref,target_date}}]}]

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "bulletins", "inventories")
REQUIRED_BULLETIN = ("bulletin_id", "network", "effective_date", "obligations")
REQUIRED_OBLIGATION = ("obligation_id", "summary", "domains")
DOMAINS = {"product", "process", "control", "contract", "system"}
DOMAIN_TO_INV = {"product": "products", "process": "processes", "control": "controls",
                 "contract": "contracts", "system": "systems"}
INV_KEYS = ("products", "processes", "controls", "contracts", "systems")
KNOWN_STATUS = {"not_started", "in_progress", "complete"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if "feed_as_of" not in doc or "max_feed_staleness_days" not in doc:
        warnings.append("no 'feed_as_of'/'max_feed_staleness_days' — feed freshness is not evaluable this run; alerts may be based on a stale bulletin feed")
    if "open_alerts" not in doc:
        warnings.append("no 'open_alerts' baseline — deduplication is disabled; every gap will be reported as new")
    if not doc.get("networks"):
        warnings.append("no 'networks' trusted-publisher list — bulletin authenticity cannot be checked against a trusted set")
    if not doc.get("owners"):
        warnings.append("no 'owners' registry — owner traceability can only flag missing owners, not unknown ones")

    bands = doc.get("readiness_bands") or {}
    for b in ("critical", "high", "medium"):
        if b in bands and _num(bands[b]) is None:
            errors.append(f"readiness_bands['{b}'] must be numeric")

    inv = doc.get("inventories") or {}
    if not isinstance(inv, dict):
        errors.append("inventories must be an object keyed by product/process/control/contract/system")
        return errors, warnings
    for k in INV_KEYS:
        if k not in inv:
            warnings.append(f"inventories has no '{k}' list — {k} references cannot be resolved and will read as dangling")

    bulletins = doc.get("bulletins") or []
    if not isinstance(bulletins, list) or not bulletins:
        errors.append("bulletins must be a non-empty list")
        return errors, warnings

    bids = set()
    for i, b in enumerate(bulletins):
        tag = f"bulletins[{i}] ({b.get('bulletin_id','?')})"
        for k in REQUIRED_BULLETIN:
            if k not in b or b[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        bid = b.get("bulletin_id")
        if bid in bids:
            errors.append(f"{tag}: duplicate bulletin_id")
        bids.add(bid)
        if b.get("effective_date") and not DATE_RE.match(str(b.get("effective_date"))):
            errors.append(f"{tag}: effective_date must start YYYY-MM-DD, got {b.get('effective_date')!r}")
        if b.get("signature_verified") is not True:
            warnings.append(f"{tag}: signature_verified is not true — bulletin will raise an authenticity alert and its obligations will be marked unverified_source")
        if not b.get("version"):
            warnings.append(f"{tag}: no version — authenticity/version cannot be confirmed")
        if not b.get("source_ref"):
            warnings.append(f"{tag}: no source_ref — bulletin provenance is not citable")

        obligations = b.get("obligations") or []
        if not isinstance(obligations, list) or not obligations:
            errors.append(f"{tag}: obligations must be a non-empty list")
            continue
        oids = set()
        for j, o in enumerate(obligations):
            otag = f"{tag}.obligations[{j}] ({o.get('obligation_id','?')})"
            for k in REQUIRED_OBLIGATION:
                if k not in o or o[k] in (None, "", []):
                    errors.append(f"{otag}: missing '{k}'")
            oid = o.get("obligation_id")
            if oid in oids:
                errors.append(f"{otag}: duplicate obligation_id within bulletin")
            oids.add(oid)
            domains = o.get("domains") or []
            impacts = o.get("impacts") or {}
            if not isinstance(impacts, dict):
                errors.append(f"{otag}: impacts must be an object keyed by inventory category")
                impacts = {}
            for d in domains:
                if d not in DOMAINS:
                    warnings.append(f"{otag}: unknown domain {d!r} (expected one of {sorted(DOMAINS)}) — not evaluable for mapping")
                    continue
                inv_key = DOMAIN_TO_INV[d]
                if not impacts.get(inv_key):
                    warnings.append(f"{otag}: declared domain '{d}' has no {inv_key} impacts — mapping completeness gap will be raised")
            if not o.get("owner"):
                warnings.append(f"{otag}: no owner — owner-traceability gap will be raised")
            impl = o.get("implementation") or {}
            status = impl.get("status")
            if status is None:
                warnings.append(f"{otag}: no implementation.status — treated as 'not_started' for readiness")
            elif status not in KNOWN_STATUS:
                warnings.append(f"{otag}: implementation.status {status!r} not in {sorted(KNOWN_STATUS)}")
            if _num(o.get("required_lead_days")) is None and _num(doc.get("min_lead_days")) is None:
                warnings.append(f"{otag}: no required_lead_days and no run-level min_lead_days — lead-time context unavailable")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
