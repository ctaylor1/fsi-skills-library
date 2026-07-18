#!/usr/bin/env python3
"""Deterministic input validation for agent-permission-scope-reviewer.

Validates an agent permission manifest before the least-privilege ruleset runs. Fails
closed on structural problems; warns on data-quality gaps that limit which rules are
evaluable for an operation.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  agent_id, as_of (YYYY-MM-DD), policy_version, environment,
  data_classifications_in_scope[], operations[{op_id, tool, operation, access_mode,
  data_classification, declared_need, writes, logged, approval_gate, revocation{recert_days,
  owner}, segregation_group, justification_ref}]

Usage:
  python validate_input.py manifest.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("agent_id", "as_of", "policy_version", "environment", "operations")
REQUIRED_OP = ("op_id", "tool", "operation", "access_mode", "data_classification")
ACCESS_MODES = {"read-only", "ask-each-time", "auto-write"}
APPROVAL_GATES = {"none", "ask-each-time", "required"}
ENVIRONMENTS = {"production", "staging", "development", "sandbox"}
SEG_GROUPS = {"read", "write", "approve"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")
    if doc["environment"] not in ENVIRONMENTS:
        errors.append(f"environment must be one of {sorted(ENVIRONMENTS)}, got {doc['environment']!r}")
    if not doc.get("data_classifications_in_scope"):
        warnings.append("no 'data_classifications_in_scope' — LP-CLASS-UNDECLARED not evaluable")

    ops = doc.get("operations") or []
    if not isinstance(ops, list) or not ops:
        errors.append("operations must be a non-empty list")
        return errors, warnings

    ids = set()
    for i, op in enumerate(ops):
        tag = f"operations[{i}] ({op.get('op_id','?')})"
        for k in REQUIRED_OP:
            if k not in op or op[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        mode = op.get("access_mode")
        if mode is not None and mode not in ACCESS_MODES:
            errors.append(f"{tag}: access_mode must be one of {sorted(ACCESS_MODES)}, got {mode!r}")
        gate = op.get("approval_gate")
        if gate is not None and gate not in APPROVAL_GATES:
            errors.append(f"{tag}: approval_gate must be one of {sorted(APPROVAL_GATES)}, got {gate!r}")
        seg = op.get("segregation_group")
        if seg is not None and seg not in SEG_GROUPS:
            errors.append(f"{tag}: segregation_group must be one of {sorted(SEG_GROUPS)}, got {seg!r}")
        oid = op.get("op_id")
        if oid in ids:
            errors.append(f"{tag}: duplicate op_id")
        ids.add(oid)

        # data-quality warnings (drive not_evaluable, not errors)
        if not op.get("declared_need") or not op.get("justification_ref"):
            warnings.append(f"{tag}: missing declared_need/justification_ref — will fire LP-NEED-01")
        if "logged" not in op:
            warnings.append(f"{tag}: no 'logged' flag — LP-LOG-OFF not evaluable for this op")
        if "approval_gate" not in op:
            warnings.append(f"{tag}: no 'approval_gate' — treated as ungated for write rules")
        if "revocation" not in op:
            warnings.append(f"{tag}: no 'revocation' block — will fire LP-REVOKE-MISSING")

    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the policy_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "scope_example.json"
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
