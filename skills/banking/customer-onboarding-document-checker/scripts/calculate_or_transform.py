#!/usr/bin/env python3
"""Deterministic onboarding-package completeness checks for customer-onboarding-document-checker.

Reads an onboarding-package file (see validate_input.py), evaluates each configured check
against the required-document checklist, attaches evidence + citations to every fired
finding, and maps the fired findings to a package-readiness band.

IMPORTANT: This produces an explainable *completeness assessment* only. It NEVER approves an
account, verifies identity, makes a KYC/CIP/sanctions determination, waives a requirement,
or opens an account. Those are human / authorized-system actions. Severities and the
readiness mapping are deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py package.json | --selftest
Prints the checks JSON to stdout. In --selftest mode also prints an internal-consistency
self-check line ending "N error(s)".
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "required_documents": [
        {"type": "government_id", "signature_required": False, "expiry_checked": True, "max_age_days": None},
        {"type": "proof_of_address", "signature_required": False, "expiry_checked": False, "max_age_days": 90},
        {"type": "tax_certification", "signature_required": True, "expiry_checked": False, "max_age_days": None},
        {"type": "signature_card", "signature_required": True, "expiry_checked": False, "max_age_days": None},
    ],
    "key_identity_fields": ["legal_name", "date_of_birth"],
    "expiring_soon_days": 30,
}
# Severity is configuration, not a per-customer judgement (see references/domain-rules.md).
SEVERITY = {
    "missing_required_document": "blocking",
    "expired_document": "blocking",
    "expiring_soon": "advisory",
    "missing_signature": "blocking",
    "illegible_document": "blocking",
    "stale_document": "blocking",
    "data_inconsistency_key": "blocking",
    "data_inconsistency_other": "advisory",
    "unresolved_exception": "blocking",
}
DISCLAIMER = ("Completeness check only; not an onboarding approval, identity verification, "
              "or KYC/CIP determination. No account has been opened.")


def _parse(d: str) -> datetime:
    return datetime.strptime(str(d)[:10], "%Y-%m-%d")


def _norm(v) -> str:
    return " ".join(str(v).strip().lower().split()) if v not in (None, "") else ""


def _doc_cite(d: dict, date_field: str = None) -> str:
    ref = d.get("source_ref", "?")
    when = d.get(date_field) if date_field else d.get("issue_date", "")
    return f"docs:{ref}@{when}" if when else f"docs:{ref}"


def _mapping(checks: list) -> str:
    blocking = any(c["fired"] and c["severity"] == "blocking" for c in checks)
    advisory = any(c["fired"] and c["severity"] == "advisory" for c in checks)
    return "Not-ready" if blocking else ("Ready-with-advisories" if advisory else "Ready")


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse(doc["as_of"])
    key_fields = cfg.get("key_identity_fields") or []
    soon = int(cfg.get("expiring_soon_days", 30))
    docs = doc.get("documents") or []
    provided = {}
    for d in docs:
        if d.get("status") == "provided":
            provided.setdefault(str(d.get("type")), []).append(d)
    by_type = {}
    for d in docs:
        by_type.setdefault(str(d.get("type")), []).append(d)

    checks = []

    def add(name, fired, reason, evidence, remediation):
        checks.append({"check": name, "severity": SEVERITY[name], "fired": bool(fired),
                       "reason": reason, "evidence": evidence, "remediation": remediation})

    # ---- per required-document checks ----
    for r in cfg["required_documents"]:
        rtype = str(r["type"])
        got = provided.get(rtype, [])
        present_any = bool(by_type.get(rtype))
        if not got:
            add("missing_required_document", True,
                f"required document '{rtype}' is not present as a provided document"
                + ("" if present_any else " (no document entry of this type)"),
                [{"required_type": rtype, "present_statuses": [x.get("status") for x in by_type.get(rtype, [])],
                  "citation": f"config:{doc.get('config_version')};required={rtype}"}],
                f"Obtain and attach a legible '{rtype}' before human review.")
            continue
        d = got[0]
        # illegible (a provided-but-unreadable doc cannot satisfy the requirement)
        if d.get("status") == "illegible":
            add("illegible_document", True,
                f"'{rtype}' is marked illegible and cannot be validated",
                [{"doc_id": d.get("doc_id"), "type": rtype, "citation": _doc_cite(d)}],
                f"Re-collect a legible copy of '{rtype}'.")
        # expiry / expiring-soon
        if r.get("expiry_checked") and d.get("expiration_date"):
            exp = _parse(d["expiration_date"])
            if exp < as_of:
                add("expired_document", True,
                    f"'{rtype}' expired on {d['expiration_date']} (as_of {doc['as_of']})",
                    [{"doc_id": d.get("doc_id"), "type": rtype, "expiration_date": d["expiration_date"],
                      "citation": _doc_cite(d, "expiration_date")}],
                    f"Obtain an unexpired '{rtype}'.")
            elif (exp - as_of).days <= soon:
                add("expiring_soon", True,
                    f"'{rtype}' expires on {d['expiration_date']} (within {soon} days of as_of)",
                    [{"doc_id": d.get("doc_id"), "type": rtype, "expiration_date": d["expiration_date"],
                      "citation": _doc_cite(d, "expiration_date")}],
                    f"Flag '{rtype}' for near-term renewal; not blocking.")
        # signature
        if r.get("signature_required") and d.get("signature_present") is False:
            add("missing_signature", True,
                f"'{rtype}' requires a signature but none is present",
                [{"doc_id": d.get("doc_id"), "type": rtype, "citation": _doc_cite(d)}],
                f"Obtain the required signature on '{rtype}'.")
        # staleness (issued too long ago)
        if r.get("max_age_days") and d.get("issue_date"):
            age = (as_of - _parse(d["issue_date"])).days
            if age > int(r["max_age_days"]):
                add("stale_document", True,
                    f"'{rtype}' issued {d['issue_date']} is {age} days old (> {r['max_age_days']} allowed)",
                    [{"doc_id": d.get("doc_id"), "type": rtype, "issue_date": d["issue_date"],
                      "citation": _doc_cite(d)}],
                    f"Obtain a '{rtype}' issued within {r['max_age_days']} days.")

    # ---- data-consistency across applicant record + provided docs (key + other fields) ----
    applicant = doc.get("applicant") or {}
    all_field_names = set(key_fields)
    for dl in provided.values():
        for d in dl:
            all_field_names |= set((d.get("fields") or {}).keys())
    for field in sorted(all_field_names):
        seen = {}  # normalized value -> list of source labels
        av = _norm(applicant.get(field))
        if av:
            seen.setdefault(av, []).append("applicant-record")
        for dl in provided.values():
            for d in dl:
                fv = _norm((d.get("fields") or {}).get(field))
                if fv:
                    seen.setdefault(fv, []).append(f"{d.get('type')}:{d.get('doc_id')}")
        if len(seen) > 1:
            is_key = field in key_fields
            name = "data_inconsistency_key" if is_key else "data_inconsistency_other"
            evidence = []
            for val, srcs in seen.items():
                for s in srcs:
                    if s == "applicant-record":
                        evidence.append({"field": field, "value": val, "source": s,
                                         "citation": f"applicant:{doc.get('package_id')};field={field}"})
                    else:
                        dtype, did = s.split(":", 1)
                        dd = next((x for x in docs if str(x.get("doc_id")) == did), {})
                        evidence.append({"field": field, "value": val, "source": s,
                                         "citation": _doc_cite(dd) if dd else f"docs:{did}"})
            add(name, True,
                f"'{field}' differs across sources: {sorted(seen)} (reconcile with the customer; pattern only)",
                evidence,
                f"Reconcile '{field}' across the application and supporting documents.")

    # ---- unresolved exceptions ----
    open_exc = [e for e in (doc.get("exceptions") or []) if e.get("status") == "open"]
    if open_exc:
        add("unresolved_exception", True,
            f"{len(open_exc)} open onboarding exception(s) remain unresolved",
            [{"exception_id": e.get("exception_id"), "type": e.get("type"), "note": e.get("note"),
              "citation": f"exceptions:pkg={doc.get('package_id')};exc={e.get('exception_id')}"} for e in open_exc],
            "Resolve or route each open exception before human certification.")

    fired = [c["check"] for c in checks if c["fired"]]
    blocking_ct = sum(1 for c in checks if c["fired"] and c["severity"] == "blocking")
    advisory_ct = sum(1 for c in checks if c["fired"] and c["severity"] == "advisory")
    remediation = [c["remediation"] for c in checks if c["fired"]]

    return {
        "checklist_id": f"cdc-{str(doc.get('package_id')).replace('*', '')}-{doc['as_of']}-0001",
        "package_id": doc.get("package_id"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "customer_type": doc.get("customer_type"),
        "product": doc.get("product"),
        "jurisdiction": doc.get("jurisdiction"),
        "checks": checks,
        "findings": fired,
        "blocking_count": blocking_ct,
        "advisory_count": advisory_ct,
        "readiness_status": _mapping(checks),
        "remediation": remediation,
        "disclaimer": DISCLAIMER,
    }


def _self_check(pack: dict) -> list[str]:
    """Internal invariants: every fired finding has cited evidence; readiness ties out."""
    errs = []
    for c in pack["checks"]:
        if c["fired"]:
            ev = c.get("evidence") or []
            if not ev:
                errs.append(f"fired check {c['check']} has no evidence")
            for row in ev:
                if not str(row.get("citation", "")).strip():
                    errs.append(f"fired check {c['check']} evidence row missing citation")
    if pack["readiness_status"] != _mapping(pack["checks"]):
        errs.append("readiness_status does not tie out to the deterministic mapping")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    pack = compute(doc)
    print(json.dumps(pack, indent=2))
    if selftest:
        errs = _self_check(pack)
        for e in errs:
            print("ERROR", e)
        print(f"compute self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
