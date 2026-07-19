#!/usr/bin/env python3
"""Deterministic input validation for cloud-security-posture-reviewer.

Validates a de-identified cloud posture export before review computation. Fails closed on
structural problems (missing identifiers, malformed dates, non-list resources); warns on
data-quality gaps that limit which policy checks are evaluable. It never renders a posture
opinion — those gaps become *findings* or *not_evaluable* entries in calculate_or_transform.py,
not input errors here.

Input schema (JSON): see references/source-map.md. Key fields:
  assessment_id, as_of (YYYY-MM-DD), config_version, cloud_provider, scope{...},
  resources[{resource_id, type, region, criticality, source_ref, ...type-specific attrs...}],
  config{max_access_key_age_days, critical_ports[], sensitive_ports[], encryptable_types[],
         allowed_regions[], required_tags[]}

Usage:
  python validate_input.py posture.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("assessment_id", "as_of", "config_version", "cloud_provider", "scope", "resources")
REQUIRED_RES = ("resource_id", "type", "source_ref")
ENCRYPTABLE_HINT = ("s3_bucket", "ebs_volume", "rds_instance", "dynamodb_table",
                    "efs_filesystem", "redshift_cluster")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if not isinstance(doc.get("scope"), dict):
        errors.append("scope must be an object (account/environment scope of the export)")

    resources = doc.get("resources")
    if not isinstance(resources, list) or not resources:
        errors.append("resources must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, r in enumerate(resources):
        tag = f"resources[{i}] ({r.get('resource_id', '?')})"
        if not isinstance(r, dict):
            errors.append(f"{tag}: resource must be an object")
            continue
        for k in REQUIRED_RES:
            if not r.get(k):
                errors.append(f"{tag}: missing '{k}'")
        rid = r.get("resource_id")
        if rid in ids:
            errors.append(f"{tag}: duplicate resource_id")
        ids.add(rid)

        rtype = str(r.get("type", "")).lower()
        if not r.get("region"):
            warnings.append(f"{tag}: no region — policy.disallowed_region not evaluable for this row")
        if "criticality" not in r:
            warnings.append(f"{tag}: no criticality label — severity may be understated")
        if rtype == "security_group" and r.get("ingress") is None:
            warnings.append(f"{tag}: security_group has no 'ingress' — network.unrestricted_ingress not evaluable")
        if rtype in ENCRYPTABLE_HINT and "encrypted" not in r:
            warnings.append(f"{tag}: encryptable resource has no 'encrypted' attribute — encryption.at_rest_disabled not evaluable")

    # structural check on config sub-fields when present
    cfg = doc.get("config") or {}
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    for k in ("critical_ports", "sensitive_ports", "encryptable_types", "allowed_regions", "required_tags"):
        if k in cfg and not isinstance(cfg[k], list):
            errors.append(f"config.{k} must be a list")
    if "max_access_key_age_days" in cfg:
        try:
            float(cfg["max_access_key_age_days"])
        except (TypeError, ValueError):
            errors.append("config.max_access_key_age_days must be numeric")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "posture_example.json"
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
