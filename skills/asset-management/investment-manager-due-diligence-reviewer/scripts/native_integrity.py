"""Canonical source binding for offline investment packages (MIT).

Bundled by tools/sync_investment_resources.py. Source binding establishes
reproducibility against supplied evidence, not authentication or approval.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math

VERSION = "1.0.0"


def _json_value(value, path="$"):
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path}: non-finite number")
        return
    if isinstance(value, list):
        for i, item in enumerate(value):
            _json_value(item, f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path}: object keys must be strings")
            _json_value(item, f"{path}.{key}")
        return
    raise ValueError(f"{path}: unsupported JSON type {type(value).__name__}")


def canonical_hash(value):
    """Hash all supplied JSON fields, rejecting non-finite/non-JSON values."""
    _json_value(value)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def attach_source(output, doc, embed=False):
    """Return a detached source-bound result; raw inputs must never be embedded."""
    if embed:
        raise ValueError("raw source embedding is unsupported; retain original input separately")
    if not isinstance(output, dict) or not isinstance(doc, dict):
        raise ValueError("output and source input must be objects")
    result = copy.deepcopy(output)
    result["input_hash"] = canonical_hash(doc)
    result["source_truth"] = "unverified"
    result.pop("source_input", None)
    return result


def validate_reconstruction(output, compute, errors, original_input=None,
                            ignored_fields=()):
    """Append failures when output differs from deterministic original-input work.

    Supply the separately retained original input. Embedded snapshots are rejected
    so internal evidence cannot leak through a native result. ``ignored_fields``
    must be a narrowly declared set checked independently by the domain validator.
    Unknown fields are rejected rather than becoming an unvalidated narrative or
    restricted-data side channel. A containing workflow should keep its envelope
    separate from this native result.
    """
    if not isinstance(output, dict):
        errors.append("output must be an object")
        return
    source = original_input
    if "source_input" in output:
        errors.append("raw source_input is forbidden in native output; retain it separately")
    if not isinstance(source, dict):
        errors.append("original input required for source-bound validation (--input)")
        return
    try:
        digest = canonical_hash(source)
        if output.get("input_hash") != digest:
            errors.append("input_hash does not match original input")
        if output.get("source_truth") != "unverified":
            errors.append("source binding must not claim source authentication")
        expected = compute(copy.deepcopy(source))
        if not isinstance(expected, dict):
            raise ValueError("calculation returned a non-object")
        expected = attach_source(expected, source)
        omitted = set(ignored_fields)
        actual_values = {k: v for k, v in output.items() if k not in omitted}
        expected_values = {k: v for k, v in expected.items() if k not in omitted}
        if canonical_hash(actual_values) != canonical_hash(expected_values):
            differences = sorted(k for k in actual_values.keys() | expected_values.keys()
                                 if k not in actual_values or k not in expected_values
                                 or canonical_hash(actual_values[k]) != canonical_hash(expected_values[k]))
            errors.append("output differs from original-input reconstruction: " + ", ".join(differences))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        errors.append(f"original-input reconstruction failed: {exc}")
