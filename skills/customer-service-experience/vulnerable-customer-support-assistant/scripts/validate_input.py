#!/usr/bin/env python3
"""Deterministic input validation for vulnerable-customer-support-assistant.

Validates a de-identified interaction record before the support-needs assessment is built.
Fails closed on structural problems; warns on data-quality gaps that limit or gate the draft
(a signal without a source_ref, an unmasked customer id, special-category data without a consent
status, an unrecognized signal type).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  config_version, customer_ref, channel, interaction_id,
  observed_signals[{signal_id, signal_type, quote, source_ref}],
  consent{special_category_data_involved, customer_consent_status},
  config{...overrides...}

Usage:
  python validate_input.py interaction.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_TOP = ("customer_ref", "channel", "observed_signals")
KNOWN_SIGNALS = {
    "bereavement", "caring_responsibility", "income_shock_job_loss", "financial_difficulty_arrears",
    "serious_illness", "disability_access_need", "mental_health_disclosed",
    "cognitive_or_memory_difficulty", "language_barrier", "low_product_understanding",
    "digital_exclusion", "domestic_or_economic_abuse", "risk_of_harm",
}
SENSITIVE_SIGNALS = {
    "serious_illness", "mental_health_disclosed", "cognitive_or_memory_difficulty",
    "domestic_or_economic_abuse", "risk_of_harm",
}
CONSENT_VALUES = {"granted", "declined", "not_captured", "not_required"}


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    signals = doc.get("observed_signals")
    if not isinstance(signals, list):
        errors.append("observed_signals must be a list")
        return errors, warnings
    # An empty list is valid: it yields a 'no support need identified' assessment.
    if not signals:
        warnings.append("no observed_signals — assessment will report no support need identified")

    ids = set()
    sensitive_present = False
    for i, s in enumerate(signals):
        tag = f"observed_signals[{i}] ({s.get('signal_id', '?')})"
        stype = s.get("signal_type")
        if not stype:
            errors.append(f"{tag}: missing 'signal_type'")
        elif stype not in KNOWN_SIGNALS:
            warnings.append(f"{tag}: unrecognized signal_type {stype!r} — it will be flagged, "
                            "not mapped to an accommodation")
        if stype in SENSITIVE_SIGNALS:
            sensitive_present = True
        if not str(s.get("quote") or "").strip():
            errors.append(f"{tag}: missing 'quote' (a support need must quote the customer)")
        if not str(s.get("source_ref") or "").strip():
            warnings.append(f"{tag}: no source_ref — cite the transcript/chat line; an uncited "
                            "signal must not be built into a suggestion")
        sid = s.get("signal_id")
        if sid in ids:
            errors.append(f"{tag}: duplicate signal_id")
        ids.add(sid)

    # Privacy: customer_ref should be masked.
    cust = str(doc.get("customer_ref", ""))
    if cust and "*" not in cust and re.search(r"\d{5,}", cust):
        warnings.append("customer_ref may be unmasked — mask to the last 4 before drafting")

    # Consent: special-category data must carry a consent status.
    consent = doc.get("consent") or {}
    status = consent.get("customer_consent_status")
    if status is not None and status not in CONSENT_VALUES:
        errors.append(f"consent.customer_consent_status {status!r} not in {sorted(CONSENT_VALUES)}")
    special = bool(consent.get("special_category_data_involved")) or sensitive_present
    if special and status not in ("granted", "declined"):
        warnings.append("special-category data involved but consent not captured — consent-dependent "
                        "accommodations will be marked pending_consent")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "interaction_example.json"
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
