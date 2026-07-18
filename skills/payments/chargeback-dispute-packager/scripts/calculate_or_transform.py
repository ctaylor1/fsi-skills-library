#!/usr/bin/env python3
"""Deterministic chargeback representment packager for chargeback-dispute-packager.

For each disputed transaction: look up the network reason code, compute the representment
(second-presentment) deadline, check that the supplied evidence satisfies the reason code's
required-evidence groups, tie every exhibit back to the disputed transaction, flag
compelling-evidence eligibility, and — only when all invariants hold — assemble a draft
representment package with an exhibit-cited narrative index.

It NEVER submits/files/transmits a representment, never makes a fraud or liability
determination, never guarantees an outcome, and never invents evidence. When the deadline
has passed, evidence is incomplete, identity does not tie, or a narrative point is
unsupported, the record is flagged (not packaged) with the reason.

Usage: python calculate_or_transform.py disputes.json | --selftest
Prints the packaging JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date, timedelta
from pathlib import Path

STANDING_NOTE = (
    "Draft representment package for human review only; this skill does not submit to any "
    "card network or acquirer, does not guarantee any dispute outcome, and every claim must "
    "be verified against current network rules before submission."
)

# Reason-code catalog (versioned contract; overridable via doc['reason_code_catalog']).
# required = list of groups; a group is satisfied if ANY of its evidence types is present.
REASON_CATALOG = {
    "VISA-10.4": {"title": "Fraud - Card-Absent Environment", "network": "VISA",
                  "window_days": 30, "category": "fraud",
                  "required": [["avs_result", "cvv_result", "three_ds_authentication"],
                               ["proof_of_delivery", "proof_of_service"],
                               ["prior_transaction_history"]]},
    "VISA-13.1": {"title": "Merchandise/Services Not Received", "network": "VISA",
                  "window_days": 30, "category": "consumer_dispute",
                  "required": [["proof_of_delivery", "proof_of_service"],
                               ["order_confirmation"], ["terms_of_service"]]},
    "VISA-13.3": {"title": "Not as Described or Defective", "network": "VISA",
                  "window_days": 30, "category": "consumer_dispute",
                  "required": [["item_description_evidence"], ["terms_of_service"],
                               ["proof_no_valid_return"]]},
    "VISA-12.6": {"title": "Duplicate Processing / Paid by Other Means", "network": "VISA",
                  "window_days": 30, "category": "processing_error",
                  "required": [["distinct_transaction_proof", "refund_proof"]]},
    "MC-4853": {"title": "Cardholder Dispute", "network": "MASTERCARD",
                "window_days": 45, "category": "consumer_dispute",
                "required": [["proof_of_delivery", "proof_of_service"],
                             ["order_confirmation"], ["terms_of_service"]]},
    "MC-4837": {"title": "No Cardholder Authorization", "network": "MASTERCARD",
                "window_days": 45, "category": "fraud",
                "required": [["avs_result", "cvv_result", "three_ds_authentication"],
                             ["proof_of_delivery", "proof_of_service"],
                             ["prior_transaction_history"]]},
}


def _as_of(doc) -> date:
    v = doc.get("as_of_date")
    return date.fromisoformat(v) if v else date.today()


def _money(v) -> float:
    return round(float(v or 0), 2)


def _deadline(d, spec, as_of):
    due = date.fromisoformat(d["chargeback_date"]) + timedelta(days=int(spec["window_days"]))
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
    cat = spec["category"]
    if cat != "fraud":
        return {"category": cat, "eligible": False, "basis": "not applicable (non-fraud reason code)"}
    priors = d.get("prior_undisputed_txns") or []
    eligible = len(priors) >= 2
    basis = (f"{len(priors)} prior undisputed transaction(s) supplied"
             if eligible else "requires >=2 prior undisputed transactions sharing cardholder identifiers")
    return {"category": cat, "eligible": eligible, "basis": basis}


def _narrative_index(d):
    ids = {e.get("exhibit_id") for e in d.get("evidence") or []}
    idx = []
    for np in d.get("narrative_points") or []:
        idx.append({"point": np.get("point"), "exhibit_id": np.get("exhibit_id"),
                    "supported": np.get("exhibit_id") in ids})
    return idx


def package_dispute(d, doc, as_of):
    catalog = {**REASON_CATALOG, **(doc.get("reason_code_catalog") or {})}
    code = d.get("reason_code")
    rec = {"dispute_id": d.get("dispute_id"), "network": d.get("network"), "reason_code": code}

    spec = catalog.get(code)
    if not spec:
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

    citations = [f"network-rules:{code}@{doc.get('ruleset_version')}"]
    citations += [f"evidence:{e.get('exhibit_id')}:{e.get('ref','')}" for e in d.get("evidence") or []]

    rec.update({
        "reason_title": spec["title"],
        "representment_due_date": due,
        "days_remaining": remaining,
        "deadline_status": dl_status,
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
        "compelling_evidence_eligible": comp["eligible"],
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
            "packages": packages, "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "disputes_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
