#!/usr/bin/env python3
"""Deterministic input validation for identity-access-reviewer.

Validates an access-review extract (identities, accounts, entitlements + config) before
findings are computed. Fails closed on structural problems; warns on data-quality gaps that
limit which findings are evaluable (e.g. missing last_login, missing SoD ruleset).

Input schema (JSON): see references/source-map.md. Key fields:
  org_unit, as_of (YYYY-MM-DD), config_version,
  config{inactivity_days, dormancy_days, certification_interval_days, max_entitlements, sod_rules[[a,b]...]},
  identities[{user_id, hr_status, display_name}],
  accounts[{account_id, user_id, account_type, last_login|null, mfa_enabled, source_ref}],
  entitlements[{grant_id, account_id, entitlement, privileged, approval_ref|null, last_certified|null, source_ref}]

Usage:
  python validate_input.py review.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_TOP = ("as_of", "config_version", "identities", "accounts", "entitlements")
REQUIRED_ACCT = ("account_id", "user_id", "account_type", "source_ref")
REQUIRED_GRANT = ("grant_id", "account_id", "entitlement", "privileged", "source_ref")
ACCOUNT_TYPES = ("human", "service", "shared")


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

    accounts = doc.get("accounts") or []
    entitlements = doc.get("entitlements") or []
    if not isinstance(accounts, list) or not accounts:
        errors.append("accounts must be a non-empty list")
    if not isinstance(entitlements, list) or not entitlements:
        errors.append("entitlements must be a non-empty list")
    if errors:
        return errors, warnings

    # identities
    idents = doc.get("identities") or []
    if not idents:
        warnings.append("identities empty — orphaned_account cannot verify owner HR status")
    for i, idn in enumerate(idents):
        if not idn.get("user_id"):
            errors.append(f"identities[{i}]: missing 'user_id'")
        if idn.get("hr_status") not in ("active", "terminated", "leave", None):
            warnings.append(f"identities[{i}] ({idn.get('user_id','?')}): unusual hr_status {idn.get('hr_status')!r}")

    # accounts
    acct_ids: set[str] = set()
    for i, a in enumerate(accounts):
        tag = f"accounts[{i}] ({a.get('account_id','?')})"
        for k in REQUIRED_ACCT:
            if a.get(k) in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if a.get("account_type") not in ACCOUNT_TYPES:
            errors.append(f"{tag}: account_type must be one of {ACCOUNT_TYPES}")
        aid = a.get("account_id")
        if aid in acct_ids:
            errors.append(f"{tag}: duplicate account_id")
        acct_ids.add(aid)
        if "mfa_enabled" not in a:
            warnings.append(f"{tag}: no mfa_enabled — privileged_without_mfa not evaluable for this account")
        if not a.get("last_login"):
            warnings.append(f"{tag}: no last_login — treated as inactive/dormant (conservative)")
        elif not DATE_RE.match(str(a.get("last_login"))):
            errors.append(f"{tag}: last_login must be YYYY-MM-DD or null")

    # entitlements
    grant_ids: set[str] = set()
    for i, g in enumerate(entitlements):
        tag = f"entitlements[{i}] ({g.get('grant_id','?')})"
        for k in REQUIRED_GRANT:
            if k not in g or g.get(k) in (None, "") and k != "privileged":
                errors.append(f"{tag}: missing '{k}'")
        if not isinstance(g.get("privileged"), bool):
            errors.append(f"{tag}: 'privileged' must be a boolean")
        gid = g.get("grant_id")
        if gid in grant_ids:
            errors.append(f"{tag}: duplicate grant_id")
        grant_ids.add(gid)
        if g.get("account_id") not in acct_ids:
            errors.append(f"{tag}: account_id {g.get('account_id')!r} not found in accounts")
        if not g.get("last_certified"):
            warnings.append(f"{tag}: no last_certified — stale_certification will fire for this grant")
        if g.get("privileged") and not g.get("approval_ref"):
            warnings.append(f"{tag}: privileged grant with no approval_ref — unapproved_privileged will fire")

    # config
    cfg = doc.get("config") or {}
    if not cfg:
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    if not cfg.get("sod_rules"):
        warnings.append("no config.sod_rules — sod_conflict not evaluable")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "access_review_example.json"
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
