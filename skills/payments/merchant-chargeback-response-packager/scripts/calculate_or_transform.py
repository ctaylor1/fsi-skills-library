#!/usr/bin/env python3
"""Offline merchant/acquirer response drafting from supplied rules and exhibits.

No built-in production rules or filing windows. A current declared rule profile,
participant/jurisdiction/stage scope and explicit cited due date are required.
Checks measure exhibit presence and identity references, not substantive sufficiency.
The output never determines compelling-evidence eligibility, liability or outcome.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path
from payment_contract import money, stable_hash, validate_rule_profile

STANDING_NOTE = (
    "Draft representment package for human review only; this skill does not submit to any "
    "card network or acquirer, does not guarantee any dispute outcome, and every claim must "
    "be verified against current network rules before submission."
)

# No built-in network rules or deadlines. Deployments supply an approved profile.


def _as_of(doc) -> date:
    v = doc.get("as_of_date")
    return date.fromisoformat(v)


def _money(v) -> float:
    return money(v)


def _deadline(d, spec, as_of):
    due = date.fromisoformat(d["response_deadline"])
    remaining = (due - as_of).days
    return due.isoformat(), remaining, ("on_time" if remaining >= 0 else "past_due")


def _evidence_check(d, spec):
    present = sorted({e.get("type") for e in d.get("evidence") or [] if e.get("type")})
    present_set = set(present)
    missing = [grp for grp in spec["required"] if not (set(grp) & present_set)]
    return {"required_groups": spec["required"], "present_types": present,
            "missing_groups": missing, "complete": not missing}


def _identity_check(d):
    txn = d.get("transaction") or {}
    mismatches = []
    if str(txn.get("currency")) != str(d.get("currency")):
        mismatches.append(f"transaction currency {txn.get('currency')!r} != dispute currency {d.get('currency')!r}")
    if _money(d.get("dispute_amount")) > _money(txn.get("amount")):
        mismatches.append(f"dispute amount {d.get('dispute_amount')} exceeds transaction amount {txn.get('amount')}")
    for e in d.get("evidence") or []:
        if e.get("txn_id") and txn.get("txn_id") and e["txn_id"] != txn["txn_id"]:
            mismatches.append(f"exhibit {e.get('exhibit_id')} references transaction {e['txn_id']} not {txn['txn_id']}")
        if e.get("arn") and txn.get("arn") and e["arn"] != txn["arn"]:
            mismatches.append(f"exhibit {e.get('exhibit_id')} references ARN {e['arn']} not {txn['arn']}")
    return {"ok": not mismatches, "mismatches": mismatches}


def _compelling(d, spec):
    priors = d.get("prior_undisputed_txns") or []
    return {"category": spec["category"], "eligibility_status": "not-determined",
            "candidate_for_review": spec["category"] == "fraud" and bool(priors),
            "basis": "Prior transactions are supplied evidence only; network-specific matching, timing and eligibility need current rule review."}


def _narrative_index(d):
    ids = {e.get("exhibit_id") for e in d.get("evidence") or []}
    idx = []
    for np in d.get("narrative_points") or []:
        idx.append({"point": np.get("point"), "exhibit_id": np.get("exhibit_id"),
                    "supported": np.get("exhibit_id") in ids})
    return idx


def package_dispute(d, doc, as_of):
    catalog = doc.get("reason_code_catalog") or {}
    code = d.get("reason_code")
    rec = {"dispute_id": d.get("dispute_id"), "network": d.get("network"), "reason_code": code}

    role = d.get("role", "merchant")
    rec["role"] = role
    profile = doc.get("rule_profile") or {}
    stage = d.get("stage")
    profile_errors = validate_rule_profile(profile, as_of.isoformat(), participant=role, jurisdiction=d.get("jurisdiction"))
    profile_ok = not profile_errors and profile.get("version") == doc.get("ruleset_version")
    if role not in {"merchant", "acquirer"} or not profile_ok or stage != profile.get("stage") or not d.get("response_deadline") or not d.get("deadline_source_ref"):
        rec.update({"status": "needs-data", "packageable": False, "citations": [], "note": "Need merchant/acquirer role, current sourced stage-specific rule profile and explicit cited deadline; no default deadline inferred."})
        return rec
    rec["rule_basis"] = profile
    spec = catalog.get(code)
    if not spec or str(spec.get("network", "")).upper() != str(d.get("network", "")).upper():
        rec.update({"status": "needs-data", "packageable": False,
                    "reason_title": None, "note": "reason_code not in catalog; supply mapping",
                    "citations": []})
        return rec

    due, remaining, dl_status = _deadline(d, spec, as_of)
    ev = _evidence_check(d, spec)
    idc = _identity_check(d)
    comp = _compelling(d, spec)
    narrative = _narrative_index(d)
    all_supported = all(n["supported"] for n in narrative) and bool(narrative)

    citations = [profile["source_ref"], d["deadline_source_ref"], f"network-rules:{code}@{doc.get('ruleset_version')}"]
    citations += [f"evidence:{e.get('exhibit_id')}:{e.get('ref','')}" for e in d.get("evidence") or []]

    rec.update({
        "reason_title": spec["title"],
        "representment_due_date": due,
        "days_remaining": remaining,
        "deadline_status": dl_status,
        "deadline_source_ref": d["deadline_source_ref"],
        "stage": stage,
        "evidence_check": ev,
        "identity_check": idc,
        "compelling_evidence": comp,
        "narrative_index": narrative,
        "citations": citations,
    })

    if dl_status == "past_due":
        rec.update({"status": "past-deadline", "packageable": False})
        return rec
    if not ev["complete"]:
        rec.update({"status": "insufficient-evidence", "packageable": False})
        return rec
    if not idc["ok"]:
        rec.update({"status": "identity-mismatch", "packageable": False})
        return rec
    if not all_supported:
        rec.update({"status": "unsupported-claim", "packageable": False})
        return rec

    rec.update({"status": "draft-representment", "packageable": True})
    rec["representment_package"] = {
        "case_reference": d.get("dispute_id"),
        "network": d.get("network"),
        "reason_code": code,
        "reason_title": spec["title"],
        "disputed_amount": f"{_money(d.get('dispute_amount'))} {d.get('currency')}",
        "transaction_identifiers": {k: (d.get("transaction") or {}).get(k)
                                    for k in ("txn_id", "arn", "auth_code", "txn_date")},
        "representment_due_date": due,
        "merchant_rebuttal_summary": "; ".join(n["point"] for n in narrative),
        "evidence_index": [{"exhibit_id": n["exhibit_id"], "supports": n["point"]} for n in narrative],
        "compelling_evidence_eligibility": comp["eligibility_status"],
        "reviewer_signoff_required": True,
    }
    return rec


def build(doc: dict) -> dict:
    as_of = _as_of(doc)
    packages = [package_dispute(d, doc, as_of) for d in doc["disputes"]]

    def _count(s):
        return sum(1 for p in packages if p.get("status") == s)

    summary = {
        "total": len(packages),
        "draft_representment": _count("draft-representment"),
        "insufficient_evidence": _count("insufficient-evidence"),
        "past_deadline": _count("past-deadline"),
        "identity_mismatch": _count("identity-mismatch"),
        "unsupported_claim": _count("unsupported-claim"),
        "needs_data": _count("needs-data"),
    }
    return {"ruleset_version": doc.get("ruleset_version"), "as_of_date": as_of.isoformat(),
            "input_snapshot_hash": stable_hash(doc), "execution_mode": "offline-draft-only", "packages": packages, "summary": summary, "approved_reason_codes": sorted(doc.get("reason_code_catalog") or {}), "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "disputes_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    from validate_input import validate
    errors, _ = validate(doc)
    if errors:
        print(json.dumps({"errors": errors})); return 1
    print(json.dumps(build(doc), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
