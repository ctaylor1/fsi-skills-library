#!/usr/bin/env python3
"""Deterministic input validation for ransomware-readiness-assessor.

Validates a readiness-posture extract (identity, critical services, third parties, exercises,
communications + config) before findings are computed. Fails closed on structural problems;
warns on data-quality gaps that limit which findings are evaluable (e.g. missing detection
coverage, missing identity posture, missing restore-test date).

Input schema (JSON): see references/source-map.md. Key fields:
  scope, as_of (YYYY-MM-DD), config_version,
  config{restore_test_interval_days, exercise_interval_days, comms_test_interval_days,
         min_detection_coverage, min_privileged_mfa_ratio},
  identity{privileged_total, privileged_with_mfa, admin_tiering, source_ref},
  critical_services[{service_id, name, tier, segmented, backup{exists,immutable,offline_copy},
                     last_restore_test|null, detection_coverage|null, dependency_map, source_ref}],
  third_parties[{tp_id, name, critical, resilience_evidence, recovery_commitment, source_ref}],
  exercises[{exercise_id, type, last_conducted|null, source_ref}],
  communications{crisis_plan, out_of_band, last_tested|null, source_ref}

Usage:
  python validate_input.py readiness.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("scope", "as_of", "config_version", "critical_services")
REQUIRED_SVC = ("service_id", "source_ref")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must be YYYY-MM-DD, got {doc['as_of']!r}")

    services = doc.get("critical_services") or []
    if not isinstance(services, list) or not services:
        errors.append("critical_services must be a non-empty list")
        return errors, warnings

    svc_ids: set[str] = set()
    for i, s in enumerate(services):
        tag = f"critical_services[{i}] ({s.get('service_id','?')})"
        for k in REQUIRED_SVC:
            if s.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        sid = s.get("service_id")
        if sid in svc_ids:
            errors.append(f"{tag}: duplicate service_id")
        svc_ids.add(sid)
        if "segmented" not in s:
            warnings.append(f"{tag}: no 'segmented' — treated as a segmentation gap (conservative)")
        backup = s.get("backup")
        if backup is None:
            warnings.append(f"{tag}: no 'backup' block — treated as a backup-coverage gap (conservative)")
        elif not isinstance(backup, dict):
            errors.append(f"{tag}: 'backup' must be an object")
        lrt = s.get("last_restore_test")
        if not lrt:
            warnings.append(f"{tag}: no last_restore_test — treated as restore_test_stale (conservative)")
        elif not DATE_RE.match(str(lrt)):
            errors.append(f"{tag}: last_restore_test must be YYYY-MM-DD or null")
        dc = s.get("detection_coverage")
        if dc is None:
            warnings.append(f"{tag}: no detection_coverage — detection_coverage_gap not evaluable for this row")
        elif not isinstance(dc, (int, float)) or not (0.0 <= float(dc) <= 1.0):
            errors.append(f"{tag}: detection_coverage must be a number in [0,1]")
        if "dependency_map" not in s:
            warnings.append(f"{tag}: no dependency_map — treated as a dependency-mapping gap (conservative)")

    # identity
    identity = doc.get("identity")
    if identity is None:
        warnings.append("no 'identity' posture — privileged_mfa_gap / admin_tiering_gap not evaluable")
    else:
        t, m = identity.get("privileged_total"), identity.get("privileged_with_mfa")
        if not isinstance(t, (int, float)) or not isinstance(m, (int, float)):
            warnings.append("identity.privileged_total/privileged_with_mfa missing or non-numeric — privileged_mfa_gap not evaluable")
        elif m > t:
            errors.append("identity.privileged_with_mfa cannot exceed privileged_total")

    # third parties
    tps = doc.get("third_parties")
    if tps is None:
        warnings.append("no 'third_parties' — third_party_resilience_gap not evaluable")
    elif not isinstance(tps, list):
        errors.append("third_parties must be a list when present")

    # exercises
    exs = doc.get("exercises")
    if exs is None:
        warnings.append("no 'exercises' — exercise_overdue not evaluable")
    else:
        for i, e in enumerate(exs):
            lc = e.get("last_conducted")
            if lc and not DATE_RE.match(str(lc)):
                errors.append(f"exercises[{i}]: last_conducted must be YYYY-MM-DD or null")

    # communications
    comms = doc.get("communications")
    if comms is None:
        warnings.append("no 'communications' posture — comms_readiness_gap not evaluable")
    elif comms.get("last_tested") and not DATE_RE.match(str(comms.get("last_tested"))):
        errors.append("communications.last_tested must be YYYY-MM-DD or null")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "readiness_example.json"
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
