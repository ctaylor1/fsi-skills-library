#!/usr/bin/env python3
"""Deterministic loan-package completeness engine for loan-package-completeness-checker.

Reads a loan package file (see validate_input.py), evaluates it against the product +
jurisdiction checklist, and emits a machine-readable completeness assessment: a list of
findings (each with a severity and cited evidence), deterministic severity counts, and a
recommended readiness disposition for a HUMAN certifier.

IMPORTANT: This produces completeness *findings and evidence* only. It never approves or
denies a loan, issues a clear-to-close or adverse action, waives a condition, or
certifies / closes / funds the loan. The readiness disposition is a deterministic function
of the findings (see references/domain-rules.md) and is a recommendation for a human, not a
decision or a system-of-record write.

Checks performed:
  1. Checklist coverage    — required applicable item with no matching document -> Blocker
                             (optional item absent -> Advisory).
  2. Signature completeness — required signer party not signed on a present doc -> Blocker.
  3. Expiration            — present doc older than its validity window -> Blocker
                             (still valid but within nearing_expiry_days -> Advisory).
  4. Cross-document consistency — field disagrees with expected_terms: money terms -> Blocker,
                             identity/address terms -> Exception.
  5. Approval envelope     — doc amount/rate exceeds approval, or approval not granted/expired
                             -> Blocker.
  6. Conditions            — outstanding prior_to_close condition -> Blocker; other outstanding
                             or waived condition -> Exception.

Usage:
  python calculate_or_transform.py loan_package.json | --selftest
Prints the assessment JSON to stdout. --selftest also prints a trailing self-check line
ending in "N error(s)" and exits non-zero if the internal tie-out fails.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {"nearing_expiry_days": 30}
MATERIAL_FIELDS = ("loan_amount", "note_rate", "term_months")   # mismatch -> Blocker
IDENTITY_FIELDS = ("borrower_name", "property_address")          # mismatch -> Exception
DISCLAIMER = ("Completeness findings and cited evidence only; this is not a lending decision "
              "or package certification, and no loan action has been taken. Human review and "
              "certification are required before the package proceeds.")


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _applies(item: dict, jurisdiction: str) -> bool:
    juris = item.get("jurisdictions") or ["ALL"]
    return "ALL" in juris or jurisdiction in juris


def _expected_readiness(counts: dict) -> str:
    if counts.get("Blocker", 0) > 0:
        return "Not-ready (blockers present)"
    if counts.get("Exception", 0) > 0:
        return "Conditional (exceptions to adjudicate)"
    return "Complete (ready for human certification)"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    jurisdiction = doc.get("jurisdiction", "ALL")
    as_of = _parse_date(doc["as_of"])
    documents = doc.get("documents") or []
    checklist = doc.get("checklist") or []
    expected = doc.get("expected_terms") or {}
    approval = doc.get("approval") or {}
    nearing = int(cfg["nearing_expiry_days"])

    findings, data_gaps = [], []
    seq = {"n": 0}

    def add(category, severity, summary, evidence):
        seq["n"] += 1
        findings.append({
            "finding_id": f"F-{seq['n']}",
            "category": category,
            "severity": severity,
            "summary": summary,
            "evidence": evidence,
        })

    def cite(ref, source):
        return {"ref": ref, "citation": source}

    docs_by_type: dict = {}
    for d in documents:
        docs_by_type.setdefault(d.get("doc_type"), []).append(d)

    items_evaluated = 0
    # 1) checklist coverage + 2) signatures + 3) expiration
    for item in checklist:
        if not _applies(item, jurisdiction):
            continue
        items_evaluated += 1
        present = docs_by_type.get(item.get("doc_type"), [])
        if not present:
            if item.get("required"):
                add("missing_document", "Blocker",
                    f"Required document '{item['doc_type']}' ({item['item_id']}) is not present in the package.",
                    [cite(f"checklist:{item['item_id']}", f"checklist:{doc.get('checklist_version','?')};item={item['item_id']}")])
            else:
                add("optional_document_absent", "Advisory",
                    f"Optional document '{item['doc_type']}' ({item['item_id']}) is not present.",
                    [cite(f"checklist:{item['item_id']}", f"checklist:{doc.get('checklist_version','?')};item={item['item_id']}")])
            continue

        for d in present:
            src = d.get("source_ref", "?")
            # signatures
            need = item.get("needs_signatures") or []
            signed = {s.get("party") for s in (d.get("signatures") or []) if s.get("signed")}
            for party in need:
                if party not in signed:
                    add("missing_signature", "Blocker",
                        f"Required '{party}' signature is missing on {d['doc_type']} ({d['doc_id']}).",
                        [cite(d["doc_id"], f"los:{src}@{d.get('effective_date','?')}")])
            # expiration
            vd = item.get("validity_days")
            eff = d.get("effective_date")
            if vd is not None and eff:
                age = (as_of - _parse_date(eff)).days
                if age > int(vd):
                    add("expired_document", "Blocker",
                        f"Required {d['doc_type']} ({d['doc_id']}) expired: {age} days old exceeds the {vd}-day validity window as of {doc['as_of']}.",
                        [cite(d["doc_id"], f"los:{src}@{eff}")])
                elif int(vd) - age <= nearing:
                    add("nearing_expiry", "Advisory",
                        f"{d['doc_type'].replace('_',' ').title()} ({d['doc_id']}) is valid but nears expiry: {int(vd) - age} day(s) remain against the {vd}-day window.",
                        [cite(d["doc_id"], f"los:{src}@{eff}")])
            elif vd is not None and not eff:
                data_gaps.append({"doc_id": d.get("doc_id"), "why": f"no effective_date; expiration not evaluable for {item['item_id']}"})

    # 4) cross-document consistency vs expected_terms
    for field, exp_val in expected.items():
        offenders = []
        for d in documents:
            fields = d.get("fields") or {}
            if field in fields and fields[field] != exp_val:
                offenders.append(d)
        if offenders:
            sev = "Blocker" if field in MATERIAL_FIELDS else "Exception"
            shown = "; ".join(f"{d['doc_id']} shows {d['fields'][field]!r}" for d in offenders)
            add("field_inconsistency", sev,
                f"'{field}' disagrees with the approved/expected value {exp_val!r}: {shown}.",
                [cite(d["doc_id"], f"los:{d.get('source_ref','?')}@{d.get('effective_date','?')}") for d in offenders])

    # 5) approval envelope
    if approval:
        approved_amt = approval.get("approved_amount")
        approved_rate = approval.get("approved_rate_max")
        aref = approval.get("approval_ref", "?")
        if approval.get("approved") is False:
            add("approval_missing", "Blocker",
                "The package shows no granted credit approval on file.",
                [cite("approval", f"approval:{aref}")])
        for d in documents:
            fields = d.get("fields") or {}
            if approved_amt is not None and isinstance(fields.get("loan_amount"), (int, float)) and fields["loan_amount"] > approved_amt:
                add("exceeds_approved_amount", "Blocker",
                    f"{d['doc_type']} ({d['doc_id']}) loan_amount {fields['loan_amount']} exceeds the approved amount {approved_amt}.",
                    [cite(d["doc_id"], f"los:{d.get('source_ref','?')}"), cite("approval", f"approval:{aref}")])
            if approved_rate is not None and isinstance(fields.get("note_rate"), (int, float)) and fields["note_rate"] > approved_rate:
                add("exceeds_approved_rate", "Blocker",
                    f"{d['doc_type']} ({d['doc_id']}) note_rate {fields['note_rate']} exceeds the approved maximum {approved_rate}.",
                    [cite(d["doc_id"], f"los:{d.get('source_ref','?')}"), cite("approval", f"approval:{aref}")])
        exp_date = approval.get("expiry_date")
        if exp_date and as_of > _parse_date(exp_date):
            add("approval_expired", "Blocker",
                f"Credit approval {aref} expired on {exp_date}, before the certification date {doc['as_of']}.",
                [cite("approval", f"approval:{aref}@{exp_date}")])

    # 6) conditions
    for cond in doc.get("conditions") or []:
        status = cond.get("status")
        if status == "cleared":
            continue
        ctype = cond.get("type", "general")
        if status == "outstanding" and ctype == "prior_to_close":
            sev = "Blocker"
            verb = "is outstanding (prior-to-close)"
        elif status == "outstanding":
            sev = "Exception"
            verb = f"is outstanding ({ctype})"
        else:  # waived
            sev = "Exception"
            verb = "is marked waived — confirm the waiver authority"
        add("open_condition", sev,
            f"Condition {cond.get('condition_id','?')} {verb}: {cond.get('description','')!r}.",
            [cite(cond.get("condition_id", "?"), f"condition:{cond.get('condition_id','?')}")])

    counts = {"Blocker": 0, "Exception": 0, "Advisory": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    readiness = _expected_readiness(counts)

    certifier_actions = []
    for f in findings:
        if f["severity"] == "Blocker":
            certifier_actions.append(f"[Blocker] {f['summary']} Resolve before certification.")
        elif f["severity"] == "Exception":
            certifier_actions.append(f"[Exception] {f['summary']} Adjudicate and document.")

    return {
        "assessment_id": f"lpcc-{doc['loan_id']}-{doc['as_of']}-0001",
        "loan_id": doc["loan_id"],
        "package_type": doc.get("package_type"),
        "as_of": doc["as_of"],
        "jurisdiction": jurisdiction,
        "product": doc.get("product"),
        "config_version": doc.get("config_version"),
        "checklist_version": doc.get("checklist_version"),
        "items_evaluated": items_evaluated,
        "findings": findings,
        "counts": counts,
        "readiness_disposition": readiness,
        "certifier_actions": certifier_actions,
        "data_gaps": data_gaps,
        "disclaimer": DISCLAIMER,
    }


def _selfcheck(out: dict) -> list[str]:
    """Internal tie-out used by --selftest: counts + readiness + evidence coverage."""
    errs = []
    recomputed = {"Blocker": 0, "Exception": 0, "Advisory": 0}
    for f in out["findings"]:
        recomputed[f["severity"]] = recomputed.get(f["severity"], 0) + 1
    if recomputed != out["counts"]:
        errs.append(f"counts tie-out failed: {recomputed} != {out['counts']}")
    if out["readiness_disposition"] != _expected_readiness(out["counts"]):
        errs.append("readiness_disposition does not match deterministic mapping")
    for f in out["findings"]:
        if not f.get("evidence"):
            errs.append(f"finding {f['finding_id']} has no evidence")
    return errs


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "loan_package.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        out = compute(doc)
        print(json.dumps(out, indent=2))
        errs = _selfcheck(out)
        for e in errs:
            print("ERROR", e)
        print(f"selftest: {len(out['findings'])} finding(s), readiness={out['readiness_disposition']!r}, {len(errs)} error(s)")
        return 1 if errs else 0
    doc = json.loads(Path(argv[0]).read_text(encoding="utf-8")) if argv else json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
