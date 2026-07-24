#!/usr/bin/env python3
"""Deterministic input validation for kpi-segment-bridge-builder.

Validates a KPI-bridge input file before any bridge is constructed. Fails closed on
structural problems and on the two HARD BOUNDARIES of this skill:

  1. NEVER FORECAST  - any bridge input whose `source_type` is forward-looking
     (forecast / projection / guidance / estimate / consensus / target / budget / plan)
     is an ERROR. This skill decomposes DISCLOSED, historical/actual results only.
  2. NEVER NORMALIZE BEYOND APPROVED MAPPINGS  - a component may only be re-mapped or
     reclassified via an approved `mapping_id`; an unapproved/ad-hoc mapping is warned on
     input and REJECTED on output.

Warns (does not block) on data-quality gaps that `validate_output` will reject: missing
provenance/citation, a walk that does not tie out, a `mapping_id` not in the approved set, a
`reconcile_to` pointing at a missing reported total.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  company_id, as_of (YYYY-MM-DD), prior_period{label,end}, current_period{label,end},
  config_version, mapping_version, currency, units, reported_totals{key->node},
  approved_mappings[{mapping_id,status,effective_date,description}],
  bridges[ {id, type('walk'|'volume_price'), metric, unit,
            walk: beginning(node), ending(node), components[
              {id,label,amount,provenance,citation,source_type,derivation,mapping_id}],
            volume_price: factors{prior_units,prior_price,current_units,current_price}(nodes),
            reconcile_to{beginning_key,ending_key} } ]
  where a node is {value, provenance, citation, source_type}.

Usage:
  python validate_input.py kpi_bridge_input.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise. Prints a line ending "N error(s)".
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("company_id", "as_of", "prior_period", "current_period",
                "config_version", "mapping_version", "bridges")
BRIDGE_TYPES = ("walk", "volume_price")
FACTOR_KEYS = ("prior_units", "prior_price", "current_units", "current_price")
TOL = 0.01

# Forward-looking source types are prohibited: this skill never forecasts. See HARD BOUNDARY.
FORBIDDEN_SOURCE_TYPES = {"forecast", "projection", "guidance", "estimate",
                          "consensus", "target", "budget", "plan", "model-output"}
# Historical / disclosed source types this skill is allowed to decompose.
ALLOWED_SOURCE_TYPES = {"reported", "disclosed", "actual", "filing", "audited", "derived"}


def _v(node):
    try:
        return float(node.get("value") if isinstance(node, dict) else node)
    except (TypeError, ValueError, AttributeError):
        return None


def _prov_cite(node):
    if isinstance(node, dict):
        return (node.get("provenance") or "").strip(), (node.get("citation") or "").strip()
    return "", ""


def _src(node):
    return (node.get("source_type") or "").strip().lower() if isinstance(node, dict) else ""


def _check_node(label, node, errors, warnings):
    """A node is {value, provenance, citation, source_type}. Numeric value required."""
    if _v(node) is None:
        errors.append(f"{label} value is not numeric")
    prov, cite = _prov_cite(node)
    if not prov:
        warnings.append(f"{label} has no provenance  - validate_output will reject the pack")
    if not cite:
        warnings.append(f"{label} has no citation  - validate_output will reject the pack")
    st = _src(node)
    if st in FORBIDDEN_SOURCE_TYPES:
        errors.append(f"{label} source_type {st!r} is forward-looking  - this skill never "
                      f"forecasts; supply a disclosed/reported/actual figure")
    elif st and st not in ALLOWED_SOURCE_TYPES:
        warnings.append(f"{label} source_type {st!r} unrecognized  - expected one of "
                        f"{sorted(ALLOWED_SOURCE_TYPES)}")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    for pk in ("prior_period", "current_period"):
        end = (doc[pk] or {}).get("end")
        if not end or not DATE_RE.match(str(end)):
            errors.append(f"{pk}.end must start YYYY-MM-DD, got {end!r}")

    approved = {m.get("mapping_id"): m for m in (doc.get("approved_mappings") or [])
                if isinstance(m, dict)}
    reported = doc.get("reported_totals") or {}
    if not reported:
        warnings.append("no reported_totals  - bridge reconciliation to disclosed totals will be skipped")
    for key, node in reported.items():
        _check_node(f"reported_totals.{key}", node, errors, warnings)

    bridges = doc.get("bridges")
    if not isinstance(bridges, list) or not bridges:
        errors.append("bridges must be a non-empty list")
        return errors, warnings

    seen_ids = set()
    for i, b in enumerate(bridges):
        tag = b.get("id") or f"#{i}"
        if not b.get("id"):
            errors.append(f"bridge {tag}: missing 'id'")
        elif b["id"] in seen_ids:
            errors.append(f"bridge {tag}: duplicate id")
        else:
            seen_ids.add(b["id"])
        if not b.get("metric"):
            errors.append(f"bridge {tag}: missing 'metric'")
        btype = b.get("type")
        if btype not in BRIDGE_TYPES:
            errors.append(f"bridge {tag}: type must be one of {BRIDGE_TYPES}, got {btype!r}")
            continue

        if btype == "walk":
            _check_node(f"bridge {tag}.beginning", b.get("beginning"), errors, warnings)
            _check_node(f"bridge {tag}.ending", b.get("ending"), errors, warnings)
            comps = b.get("components")
            if not isinstance(comps, list) or not comps:
                errors.append(f"bridge {tag}: walk needs a non-empty 'components' list")
                comps = []
            csum = 0.0
            for j, c in enumerate(comps):
                ctag = f"bridge {tag}.component[{c.get('id', j)}]"
                amt = _v(c.get("amount"))
                if amt is None:
                    errors.append(f"{ctag}: amount is not numeric")
                else:
                    csum += amt
                prov, cite = _prov_cite(c)
                if not prov:
                    warnings.append(f"{ctag}: no provenance  - validate_output will reject the pack")
                if not cite:
                    warnings.append(f"{ctag}: no citation  - validate_output will reject the pack")
                st = _src(c)
                if st in FORBIDDEN_SOURCE_TYPES:
                    errors.append(f"{ctag}: source_type {st!r} is forward-looking  - this skill "
                                  f"never forecasts a bridge component")
                elif st and st not in ALLOWED_SOURCE_TYPES:
                    warnings.append(f"{ctag}: source_type {st!r} unrecognized")
                if (c.get("derivation") or "").strip().lower() == "mapping":
                    mid = (c.get("mapping_id") or "").strip()
                    if not mid:
                        errors.append(f"{ctag}: derivation 'mapping' requires a mapping_id")
                    elif mid not in approved:
                        warnings.append(f"{ctag}: mapping_id {mid!r} not in approved_mappings  - "
                                        f"validate_output rejects unapproved normalization")
                    elif (approved[mid].get("status") or "").lower() != "approved":
                        warnings.append(f"{ctag}: mapping_id {mid!r} status is not 'approved'")
            beg, end = _v(b.get("beginning")), _v(b.get("ending"))
            if None not in (beg, end) and abs(beg + csum - end) > TOL:
                warnings.append(f"bridge {tag}: walk does not tie out "
                                f"(beginning {beg} + sum(components) {round(csum, 4)} != ending {end}); "
                                f"validate_output will reject it")

        elif btype == "volume_price":
            factors = b.get("factors") or {}
            for fk in FACTOR_KEYS:
                if fk not in factors:
                    errors.append(f"bridge {tag}: volume_price requires factors.{fk}")
                else:
                    _check_node(f"bridge {tag}.factors.{fk}", factors[fk], errors, warnings)

        rc = b.get("reconcile_to") or {}
        for side in ("beginning_key", "ending_key"):
            key = rc.get(side)
            if key and key not in reported:
                warnings.append(f"bridge {tag}: reconcile_to.{side} {key!r} not in reported_totals")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "kpi_bridge_input.json"
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
