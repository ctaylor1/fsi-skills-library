#!/usr/bin/env python3
"""Deterministic input validation for suspicious-activity-report-drafter.

Validates an approved-investigation SAR case-intake file before a SAR draft package is
assembled. Fails closed (exit 1) on structural problems; warns on data gaps and tie-out
breaks that force a `needs-evidence` package (never a guess). Stdlib-only, self-contained,
operates on a documented JSON schema — no live calls.

Input schema (JSON): see references/source-map.md. Key fields:
  config_version, template_version, jurisdiction, case_id,
  case_approved_for_sar (bool), approving_investigation,
  filing_context{filing_type, prior_sar_ref, activity_detected_date, regulatory_deadline_days},
  subjects[{subject_ref, role, type, name_masked, identifiers_masked[], relationship}],
  accounts_instruments[{account_ref, type, instruments[]}],
  activity{period{from,to}, aggregate_amount, currency, transaction_count},
  transactions[{txn_id, date, amount, instrument, subject_ref, counterparty_ref, source_ref}],
  typologies[{code, observed_indicators[]}],
  typology_library{<code>: {label, required_indicators[]}},
  narrative_inputs{who, what, when, where, why, how},
  evidence[{fact, citation}],
  investigation_rationale{summary, citations[]},
  required_approvals[], recorded_approvals[{role, approver, date}]

Usage: python validate_input.py case.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys, math
from calculate_or_transform import _approval_valid, _amount_tie_out, _investigation_rationale
from pathlib import Path
from native_integrity import canonical_hash

REQUIRED_TOP = ("config_version", "as_of", "case_id", "subjects", "transactions", "activity",
                "required_approvals")
REQUIRED_TXN = ("txn_id", "date", "amount", "instrument", "subject_ref", "source_ref")
REQUIRED_SUBJECT = ("subject_ref", "role", "type", "name_masked", "relationship")
WHO_WHAT = ("who", "what", "when", "where", "why", "how")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _validate_impl(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    # Hard boundary: a SAR draft is only produced from an approved, adjudicated investigation.
    if doc.get("case_approved_for_sar") is not True:
        warnings.append("case_approved_for_sar is not true -> HARD BOUNDARY: package will be "
                        "blocked for accountable FIU investigator review; financial-crime-case-investigator "
                        "is planned, not installed. Do not wait for case closure to meet reporting obligations")
    if not _approval_valid(doc.get("drafting_authorization") or {}, doc):
        warnings.append("missing, stale or unbound supplied drafting authorization -> blocked; issuer authority is not authenticated offline")

    subjects = doc.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        errors.append("subjects must be a non-empty list")
        return errors, warnings
    subj_refs = set()
    for i, s in enumerate(subjects):
        tag = f"subjects[{i}] ({s.get('subject_ref','?')})"
        for k in REQUIRED_SUBJECT:
            if k not in s or s[k] in (None, "", []):
                errors.append(f"{tag}: missing '{k}'")
        subj_refs.add(s.get("subject_ref"))
    if not any((s.get("role") == "primary") for s in subjects):
        warnings.append("no subject has role 'primary' -> confirm the principal subject before packaging")

    txns = doc.get("transactions")
    if not isinstance(txns, list) or not txns:
        errors.append("transactions must be a non-empty list")
        return errors, warnings
    txn_total = 0.0
    dates = []
    txn_ids = set()
    for i, t in enumerate(txns):
        tag = f"transactions[{i}] ({t.get('txn_id','?')})"
        for k in REQUIRED_TXN:
            if k not in t or t[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if not _num(t.get("amount")):
            errors.append(f"{tag}: amount must be a number")
        else:
            txn_total += float(t["amount"])
        if t.get("date"):
            dates.append(t["date"])
        if t.get("txn_id") in txn_ids:
            errors.append(f"{tag}: duplicate txn_id")
        txn_ids.add(t.get("txn_id"))
        ref = t.get("subject_ref")
        if ref and ref not in subj_refs:
            warnings.append(f"{tag}: subject_ref {ref!r} not in subjects -> party-coverage gap (needs-evidence)")
        cref = t.get("counterparty_ref")
        if cref and cref not in subj_refs:
            warnings.append(f"{tag}: counterparty_ref {cref!r} not in subjects -> party-coverage gap (needs-evidence)")
    if errors:
        return errors, warnings

    act = doc.get("activity") or {}
    if not isinstance(act, dict):
        errors.append("activity must be an object")
        return errors, warnings
    per = act.get("period") or {}
    if not (per.get("from") and per.get("to")):
        errors.append("activity.period requires 'from' and 'to'")
    if not _num(act.get("aggregate_amount")):
        errors.append("activity.aggregate_amount must be a number")

    # Tie-out warnings (do not fail; they force needs-evidence downstream).
    if _num(act.get("aggregate_amount")) and abs(txn_total - float(act["aggregate_amount"])) > 0.005:
        warnings.append(f"amount tie-out break: transactions sum {txn_total:g} != aggregate "
                        f"{act['aggregate_amount']:g} -> needs-evidence")
    if dates and per.get("from") and min(dates) != per.get("from"):
        warnings.append(f"chronology tie-out: earliest txn {min(dates)} != period.from {per.get('from')} -> needs-evidence")
    if dates and per.get("to") and max(dates) != per.get("to"):
        warnings.append(f"chronology tie-out: latest txn {max(dates)} != period.to {per.get('to')} -> needs-evidence")
    if act.get("transaction_count") is not None and act.get("transaction_count") != len(txns):
        warnings.append(f"transaction_count {act.get('transaction_count')} != actual {len(txns)} -> needs-evidence")

    req_appr = doc.get("required_approvals")
    if not isinstance(req_appr, list) or not req_appr:
        errors.append("required_approvals must be a non-empty list of approver roles")

    # Content-completeness warnings.
    lib = doc.get("typology_library")
    tys = doc.get("typologies")
    if tys and (not isinstance(lib, dict) or not lib):
        warnings.append("no typology_library provided -> typology consistency cannot be checked (needs-evidence)")
    ni = doc.get("narrative_inputs") or {}
    for w in WHO_WHAT:
        if not str(ni.get(w) or "").strip():
            warnings.append(f"narrative_inputs.{w} missing -> 5W+H incomplete (needs-evidence)")
    if not doc.get("evidence"):
        warnings.append("no evidence[] provided -> narrative facts will be uncited (needs-evidence)")
    if not (doc.get("investigation_rationale") or {}).get("citations"):
        warnings.append("investigation_rationale has no citations -> unsupported rationale (needs-evidence)")
    for issue in _amount_tie_out(doc)["breaks"]:
        warnings.append("chronology/tie-out gap -> needs-evidence: " + issue)
    for issue in _investigation_rationale(doc)["gaps"]:
        warnings.append("rationale gap -> needs-evidence: " + issue)
    if doc.get("recorded_approvals") is None:
        warnings.append("no recorded_approvals -> approval ledger will list all required approvals as pending (expected for a draft)")

    return errors, warnings


INPUT_SHAPE = {
    "config_version": str, "case_id": str, "as_of": str,
    "subjects": [{"subject_ref": str, "role": str, "type": str, "name_masked": str, "relationship": str, "identifiers_masked": [str]}],
    "transactions": [{"txn_id": str, "date": str, "amount": (int, float), "subject_ref": str, "counterparty_ref": str, "source_ref": str}],
    "activity": {"period": {"from": str, "to": str}, "aggregate_amount": (int, float)},
    "required_approvals": [str], "recorded_approvals": [{}], "drafting_authorization": {},
    "evidence": [{"evidence_id": str, "fact": str, "citation": str}],
    "investigation_rationale": {"summary": str, "evidence_ids": [str], "citations": [str]},
    "filing_context": {}, "accounts_instruments": [{"instruments": [str]}],
    "narrative_inputs": {key: str for key in WHO_WHAT},
    "narrative_evidence_ids": {key: [str] for key in WHO_WHAT},
    "typologies": [{"observed_indicators": [str], "indicator_evidence": {}}], "typology_library": {},
}

def _shape_errors(value, shape, path="$", optional=False):
    """Reject malformed supplied containers; absent evidence remains a domain gap."""
    if value is None and optional:
        return []
    if isinstance(shape, dict):
        if not isinstance(value, dict):
            return [f"{path} must be an object"]
        return [error for key, child in shape.items() if key in value
                for error in _shape_errors(value[key], child, f"{path}.{key}", optional=True)]
    if isinstance(shape, list):
        if not isinstance(value, list):
            return [f"{path} must be a list"]
        return [error for index, item in enumerate(value)
                for error in _shape_errors(item, shape[0], f"{path}[{index}]")]
    if not isinstance(value, shape) or (shape == (int, float) and isinstance(value, bool)):
        return [f"{path} has an invalid type"]
    return []


def validate(doc):
    """Validate the same intake boundary used by public calculators and native replay."""
    try:
        canonical_hash(doc)  # Reject non-finite and non-JSON values, including optional fields.
        errors = _shape_errors(doc, INPUT_SHAPE)
        if errors:
            return errors, []
        return _validate_impl(doc)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        return ["malformed input: " + str(exc)], []


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sar_case_example.json"
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
