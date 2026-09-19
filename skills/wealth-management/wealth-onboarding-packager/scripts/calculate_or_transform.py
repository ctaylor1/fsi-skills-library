#!/usr/bin/env python3
"""Assemble supplied relationship/account evidence against an explicit firm checklist."""

import json
import sys
from pathlib import Path
from wealth_contract import iso_date, make_output, nonempty, source_errors, validate_envelope

SKILL = "wealth-onboarding-packager"
REGISTRATIONS = {"individual", "joint", "ira", "entity", "trust"}
REVIEW_KINDS = {"kyc", "sanctions", "beneficial-ownership"}
DISCLAIMER = "Draft onboarding evidence package for authorized human review. Review-ready does not mean approved or permitted to open. No KYC or sanctions decision, account opening, transfer, communication, or system change has occurred."


def assess(doc):
    errors = validate_envelope(doc)
    findings = []
    if errors:
        return errors, findings

    def gap(code, message, **extra):
        findings.append({"code": code, "message": message, **extra})

    def sourced(record, label):
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            return False
        issues = source_errors(record.get("source_ids"), doc)
        for issue in issues:
            gap("source-gap", f"{label}: {issue}")
        return not issues

    def records(key, idkey):
        rows = doc.get(key)
        if rows is None:
            gap("missing-data", f"{key} is not supplied")
            return []
        if not isinstance(rows, list) or len(rows) > 1000:
            errors.append(f"{key} must be a list of at most 1000 records")
            return []
        seen = set()
        for row in rows:
            if not sourced(row, key):
                if not isinstance(row, dict):
                    continue
            rid = row.get(idkey)
            if not nonempty(rid) or rid in seen:
                errors.append(f"{key} requires unique nonempty {idkey}")
            else:
                seen.add(rid)
        return [r for r in rows if isinstance(r, dict)]

    policy = doc.get("policy")
    if not isinstance(policy, dict):
        gap(
            "policy-gap",
            "versioned firm checklist and applicability policy missing; no universal AML checklist substituted",
        )
        policy = {}
    else:
        sourced(policy, "policy")
        for key in ("version", "owner"):
            if not nonempty(policy.get(key)):
                gap("policy-gap", f"policy.{key} is required")
        for key in ("capacity", "jurisdiction"):
            if policy.get(key) != doc["engagement"][key]:
                gap("policy-scope", f"policy.{key} must match engagement")
    relationship = doc.get("relationship")
    if not isinstance(relationship, dict):
        gap("relationship-gap", "relationship scope not supplied")
    else:
        sourced(relationship, "relationship")
        if not nonempty(relationship.get("relationship_id")) or not nonempty(relationship.get("service_scope")):
            gap("relationship-gap", "relationship identifier and service scope must be recorded")
        if relationship.get("engagement_document_status") != "received":
            gap("engagement-gap", "engagement evidence is missing, pending or conflicted")
    accounts = records("accounts", "account_id")
    parties = records("parties", "party_id")
    docs = records("documents", "document_id")
    consents = records("consents", "consent_id")
    reviews = records("external_reviews", "review_id")
    if not accounts:
        gap("account-gap", "at least one proposed account is needed")
    if not parties:
        gap("identity-gap", "party evidence is missing")
    pids = {p.get("party_id") for p in parties if nonempty(p.get("party_id"))}
    aids = {a.get("account_id") for a in accounts if nonempty(a.get("account_id"))}
    for party in parties:
        if party.get("identity_record_status") != "received":
            gap("identity-gap", f"{party.get('party_id')}: identity evidence incomplete or conflicted")
        if party.get("role") not in ("owner", "authorized-person", "beneficial-owner", "trustee"):
            gap("authority-gap", f"{party.get('party_id')}: relationship role unknown")
    rules = policy.get("account_requirements")
    if not isinstance(rules, dict):
        gap("policy-gap", "account_requirements must explicitly cover each registration")
        rules = {}
    consent_requirements = policy.get("consent_requirements")
    if (
        not isinstance(consent_requirements, list)
        or not consent_requirements
        or any(not nonempty(x) for x in consent_requirements)
    ):
        gap("policy-gap", "explicit nonempty consent requirements missing")
        consent_requirements = []
    review_policy = policy.get("external_review_requirements")
    if not isinstance(review_policy, dict):
        gap(
            "policy-gap",
            "external review applicability must explicitly address kyc, sanctions and beneficial-ownership",
        )
        review_policy = {}
    else:
        for kind in sorted(REVIEW_KINDS - set(review_policy)):
            gap("policy-gap", f"{kind}: external review applicability is not declared")
        for kind in sorted(set(review_policy) - REVIEW_KINDS):
            gap("policy-gap", f"{kind}: unsupported external review applicability declaration")
        # Preserve every independently declared requirement even when another entry is
        # missing or malformed. A policy gap must not hide known specialist-review gaps.
        review_policy = {kind: rule for kind, rule in review_policy.items() if kind in REVIEW_KINDS}
    for kind, rule in review_policy.items():
        if (
            not isinstance(rule, dict)
            or rule.get("required") not in (True, False)
            or not isinstance(rule.get("required"), bool)
            or not nonempty(rule.get("rationale"))
        ):
            gap("policy-gap", f"{kind}: applicability requires boolean required and sourced-policy rationale")
    if errors:
        return errors, findings
    for account in accounts:
        aid = account["account_id"]
        reg = account.get("registration")
        if not isinstance(reg, str) or reg not in REGISTRATIONS:
            gap("registration-gap", f"{aid}: unsupported or missing registration")
        owners = account.get("owner_ids")
        authorized = account.get("authorized_person_ids")
        if not isinstance(owners, list) or not owners or any(not isinstance(x, str) or x not in pids for x in owners):
            gap("identity-gap", f"{aid}: owners must resolve to supplied party records")
            owners = []
        if (
            not isinstance(authorized, list)
            or not authorized
            or any(not isinstance(x, str) or x not in pids for x in authorized)
        ):
            gap("authority-gap", f"{aid}: authorized persons must resolve to supplied party records")
            authorized = []
        if account.get("authority_record_status") != "received":
            gap("authority-gap", f"{aid}: evidence of authority incomplete or conflicted")
        required = rules.get(reg) if isinstance(reg, str) else None
        if not isinstance(required, list) or not required or any(not nonempty(x) for x in required):
            gap("policy-gap", f"{aid}: no explicit document checklist for registration {reg}")
            required = []
        for kind in required:
            matches = [d for d in docs if d.get("account_id") == aid and d.get("kind") == kind]
            if not matches:
                gap("document-gap", f"{aid}: missing required {kind}")
            for item in matches:
                if item.get("status") != "received":
                    gap("document-gap", f"{aid}: {kind} is not received/current")
                if not iso_date(item.get("valid_until")) or iso_date(item["valid_until"]) < iso_date(doc["as_of"]):
                    gap("document-gap", f"{aid}: {kind} expiry/review date missing or stale")
        for pid in set(owners + authorized):
            for scope in consent_requirements:
                matches = [c for c in consents if c.get("party_id") == pid and c.get("scope") == scope]
                if not matches or any(c.get("status") != "recorded" for c in matches):
                    gap("consent-gap", f"{pid}: {scope} consent evidence missing, declined or conflicting")
        for kind, rule in review_policy.items():
            if not isinstance(rule, dict) or rule.get("required") is not True:
                continue
            matches = [r for r in reviews if r.get("kind") == kind and r.get("account_id") == aid]
            if not matches:
                gap("external-review-gap", f"{aid}: {kind} outcome not supplied; route to authorized owner")
            for review in matches:
                if review.get("status") != "completed-by-owner" or not nonempty(review.get("owner_reference")):
                    gap(
                        "external-review-gap", f"{aid}: {kind} is pending/escalated or lacks authorized-owner reference"
                    )
                if review.get("outcome") != "no-unresolved-issues-recorded":
                    gap(
                        "external-review-gap",
                        f"{aid}: {kind} has no explicit owner-recorded outcome without unresolved issues",
                    )
                covered = review.get("party_ids")
                if not isinstance(covered, list) or not set(owners).issubset(
                    {x for x in covered if isinstance(x, str)}
                ):
                    gap("external-review-gap", f"{aid}: {kind} outcome does not cover all owners")
    for record in docs + reviews:
        if record.get("account_id") not in aids:
            gap("identity-gap", "document/review references an unknown account")
    for record in consents:
        if record.get("party_id") not in pids:
            gap("identity-gap", "consent references an unknown party")
    return errors, findings


def compute(doc):
    errors, findings = assess(doc)
    if errors:
        raise ValueError("; ".join(errors))
    policy = doc.get("policy") or {}
    result = {
        "relationship_id": (doc.get("relationship") or {}).get("relationship_id"),
        "policy_version": policy.get("version"),
        "account_register": [
            {
                "account_id": a.get("account_id"),
                "registration": a.get("registration"),
                "owner_ids": a.get("owner_ids"),
                "authorized_person_ids": a.get("authorized_person_ids"),
                "source_ids": a.get("source_ids"),
            }
            for a in doc.get("accounts", [])
        ],
        "document_register": doc.get("documents", []),
        "consent_register": doc.get("consents", []),
        "external_review_evidence": doc.get("external_reviews", []),
        "applicability": policy.get("external_review_requirements", {}),
        "next_steps": [{"owner": "authorized onboarding reviewer", "task": f["message"]} for f in findings],
        "disclaimer": DISCLAIMER,
    }
    out = make_output(SKILL, doc, result, findings)
    out["input_snapshot"] = doc
    return out


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/onboarding_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        print(
            json.dumps(compute(json.loads(path.read_text() if path else sys.stdin.read())), indent=2, allow_nan=False)
        )
        return 0
    except (ValueError, TypeError, KeyError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
