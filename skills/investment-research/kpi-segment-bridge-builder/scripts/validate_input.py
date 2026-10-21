#!/usr/bin/env python3
"""Bounded input validation for kpi-segment-bridge-builder.

Finite JSON numbers, typed shapes, dates, identifiers and method domains are checked.
Malformed inputs return validation errors. See references/domain-rules.md for supported scope.
"""
from __future__ import annotations
import json, re, sys, math
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
    return _number(node)


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


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
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


def _number(value):
    if isinstance(value, dict):
        value = value.get("value")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def _base_domains(doc):
    from datetime import date
    errors = []
    for key in ("as_of", "as_of_date", "valuation_date"):
        if key in doc:
            try:
                date.fromisoformat(doc[key])
            except (TypeError, ValueError):
                errors.append(key + " must be an exact valid YYYY-MM-DD date")
    for key in ("company", "company_id", "entity_id", "config_version", "analysis_id", "model_id", "currency", "units"):
        if key in doc and (not isinstance(doc[key], str) or not doc[key].strip()):
            errors.append(key + " must be a nonempty string")
    return errors


def _unique(rows, field, label, errors):
    seen = set()
    for row in rows:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(label + ": " + field + " must be a nonempty string")
        elif value in seen:
            errors.append(label + ": duplicate " + field + " " + value)
        else:
            seen.add(value)

def _phase1_shapes(doc):
    errors = []
    for key in ['prior_period', 'current_period', 'reported_totals']:
        if key in doc and not isinstance(doc[key], dict):
            errors.append(key + " must be an object")
    for key in ['bridges', 'approved_mappings']:
        if key in doc and (not isinstance(doc[key], list) or any(not isinstance(row, dict) for row in doc[key])):
            errors.append(key + " must be a list of objects")
    if errors:
        return errors
    for bridge in doc.get("bridges", []):
        if "components" in bridge and (not isinstance(bridge["components"], list) or any(not isinstance(row, dict) for row in bridge["components"])):
            errors.append("components must be a list of objects")
        for key in ("factors", "reconcile_to"):
            if key in bridge and not isinstance(bridge[key], dict):
                errors.append(key + " must be an object")
    return errors

def _phase1_domains(doc):
    from datetime import date
    errors = _base_domains(doc)
    prior = date.fromisoformat(doc["prior_period"]["end"])
    current = date.fromisoformat(doc["current_period"]["end"])
    if not prior < current <= date.fromisoformat(doc["as_of"]):
        errors.append("closed periods must satisfy prior < current <= as_of")
    mappings = doc.get("approved_mappings", [])
    _unique(mappings, "mapping_id", "approved_mappings", errors)
    approved = {m["mapping_id"]: m for m in mappings}
    for m in mappings:
        effective = date.fromisoformat(m.get("effective_date", ""))
        if effective > prior:
            errors.append("mapping " + m["mapping_id"] + " must be effective on/before the prior period end to bridge both periods")
        if m.get("status", "").lower() != "approved":
            errors.append("mapping " + m["mapping_id"] + " is not approved")
    for bridge in doc["bridges"]:
        _unique(bridge.get("components", []), "id", "bridge components", errors)
        nodes = list(doc.get("reported_totals", {}).values()) + list(bridge.get("factors", {}).values()) + bridge.get("components", [])
        if bridge.get("type") == "walk":
            nodes += [bridge.get("beginning"), bridge.get("ending")]
        for node in nodes:
            provenance, citation = _prov_cite(node)
            if not provenance or not citation or _src(node) not in ALLOWED_SOURCE_TYPES:
                errors.append("historical inputs require provenance, citation and a permitted source_type")
        rc = bridge.get("reconcile_to", {})
        for key in ("beginning_key", "ending_key"):
            if rc and (not rc.get(key) or rc[key] not in doc.get("reported_totals", {})):
                errors.append("bridge " + bridge["id"] + " requires authoritative reported total for " + key)
        for component in bridge.get("components", []):
            if component.get("derivation") == "mapping" and component.get("mapping_id") not in approved:
                errors.append("mapping component requires approved effective mapping")
    return errors

def _strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON object key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return _read_json(text, object_pairs_hook=pairs, parse_constant=constant)

def _local_module(filename):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_local_" + filename.replace(".", "_"), Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def validate(doc):
    """Reject invalid JSON/shapes without treating an exception as a passing validation."""
    if not isinstance(doc, dict):
        return ["input must be an object"], []
    try:
        _local_module("native_integrity.py").canonical_hash(doc)
        shape_errors = _phase1_shapes(doc)
        if shape_errors:
            return shape_errors, []
        errors, warnings = _validate_native(doc)
        if not errors:
            errors.extend(_phase1_domains(doc))
        return errors, warnings
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        return ["invalid input: " + str(exc)], []

def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "kpi_bridge_input.json"
        doc = _strict_json(p.read_text(encoding="utf-8"))
    elif argv:
        doc = _strict_json(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = _strict_json(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


_main_checked = main

def main(argv):
    try:
        return _main_checked(argv)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError, OSError) as exc:
        print("ERROR", str(exc), file=sys.stderr)
        return 1

_validate_phase1 = validate

def validate(doc):
    if isinstance(doc, dict) and doc.get('schema_version') == 'ir-phase2/1.0':
        try:
            _local_module('phase2_domain.py').validate_document(doc)
            return [], []
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
            return ['invalid Phase2 input: ' + str(exc)], []
    return _validate_phase1(doc)

def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
