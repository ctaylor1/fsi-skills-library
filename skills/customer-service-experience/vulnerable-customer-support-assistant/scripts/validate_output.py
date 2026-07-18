#!/usr/bin/env python3
"""Deterministic output validation for vulnerable-customer-support-assistant.

Enforces the R2 "Draft & package" guardrails before a support-needs assessment is presented to
the handling agent for review:
  1. Every observed signal carries a citation (no uncited assertion).
  2. Every suggested accommodation is in the APPROVED catalog and traced to >=1 cited signal
     (no unsupported/unapproved claim).
  3. Every suggested referral route (primary + additional) is in the approved route set.
  4. The required output-template sections are all present (template fidelity).
  5. No prohibited language: diagnostic, discriminatory / mental-capacity determination, or
     financial/medical/legal advice (regex screen over the rendered document + narrative).
  6. record_update is "proposed" and NOT applied (no autonomous system-of-record change).
  7. The draft is marked human_review_required (external-delivery approval gate).
  8. The standing note is present.

Fails closed on any miss so a diagnostic, discriminatory, unsupported, or auto-applied draft
cannot be presented as ready.

Usage: python validate_output.py assessment.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

APPROVED_ACCOMMODATIONS = {
    "ACC-COMMS-ALT", "ACC-EXTRA-TIME", "ACC-THIRD-PARTY", "ACC-INTERPRETER",
    "ACC-QUIET-CHANNEL", "ACC-SPECIALIST-CALLBACK", "ACC-FORBEARANCE-SIGNPOST",
    "ACC-EXTERNAL-SUPPORT-SIGNPOST",
}
APPROVED_ROUTES = {
    "safeguarding-team", "internal-vulnerability-specialist",
    "financial-difficulty-team", "external-support-signpost",
}
REQUIRED_SECTIONS = [
    "Support-needs assessment (DRAFT)",
    "Observed signals",
    "Possible support needs",
    "Suggested accommodations",
    "Suggested referral",
    "Consent and approvals",
    "What this is not",
]
STANDING_NOTE = (
    "Draft support-needs suggestions for human review only; this is not a diagnosis and not a "
    "determination about the customer, it applies no vulnerability marker or accommodation to any "
    "system of record and sends nothing to the customer, and every suggestion is drawn from the "
    "approved catalog and must be confirmed with the customer and an authorized colleague before "
    "anything is applied."
)

# Clinical conclusions about the customer — prohibited (a signal is context, not a diagnosis).
# Patterns are assertion-specific so negated safe boilerplate ("not a diagnosis") does not trip;
# the scan also strips the customer's own quoted words so their disclosures are never flagged.
DIAGNOSTIC_PATTERNS = [
    r"\b(diagnos(ed|is) (with|of)|we diagnos(e|ed))\b",
    r"\bsuffers from\b",
    r"\b(the customer|they|she|he) (has|have) (dementia|alzheimer'?s|depression|anxiety disorder|bipolar|schizophrenia|ptsd|a mental illness)\b",
    r"\b(the customer|they|she|he) (is|are) (mentally ill|clinically depressed|demented|senile)\b",
    r"\b(clearly|obviously|definitely) has\b",
    r"\bwe (have )?determined (that )?the customer (is|has)\b",
]
# Mental-capacity / fitness determinations and discriminatory service limits — prohibited.
DISCRIMINATORY_PATTERNS = [
    r"\blacks (mental )?capacity\b", r"\bmentally incompetent\b", r"\bnot competent\b",
    r"\b(cannot|can'?t|unable to) manage (their|his|her) (own )?(money|account|finances)\b",
    r"\b(too (old|confused|frail)) to\b",
    r"\b(deny|refuse|decline|withhold|restrict|block) (them|service|support|access|the account)\b",
    r"\bshould not be (allowed|permitted|trusted)\b",
]
# Financial / investment / legal / medical advice — prohibited (signpost instead).
ADVICE_PATTERNS = [
    r"\byou should (invest|refinance|consolidate your debt|take out (a|another) loan|withdraw|move your money|switch)\b",
    r"\bi (recommend|advise) (that )?you (invest|borrow|refinance|consolidate|sell|buy|switch)\b",
    r"\bas your (financial|investment|legal|tax) (advisor|adviser|attorney)\b",
    r"\bthis is (financial|investment|legal) advice\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []

    signals = doc.get("observed_signals")
    if signals is None:
        return ["assessment output has no observed_signals field"]

    aid = doc.get("assessment_id", "?")

    # 1. Every observed signal cited.
    for s in signals:
        if not str(s.get("citation") or s.get("source_ref") or "").strip():
            errors.append(f"{aid}: observed signal {s.get('signal_id')!r} missing citation "
                          "(no uncited assertion)")

    # 2. Accommodations: approved + supported.
    for acc in doc.get("suggested_accommodations") or []:
        code = acc.get("code")
        if code not in APPROVED_ACCOMMODATIONS:
            errors.append(f"{aid}: unapproved accommodation {code!r} (not in approved catalog)")
        if not (acc.get("supporting_signals") or []):
            errors.append(f"{aid}: unsupported accommodation {code!r} — no cited supporting signal")

    # 3. Referral routes approved.
    ref = doc.get("suggested_referral")
    if ref:
        if ref.get("route") not in APPROVED_ROUTES:
            errors.append(f"{aid}: unapproved referral route {ref.get('route')!r}")
    for r in doc.get("additional_routes") or []:
        if r not in APPROVED_ROUTES:
            errors.append(f"{aid}: unapproved referral route {r!r}")

    # 4. Required template sections present (template fidelity).
    document = str(doc.get("document") or "")
    for sec in REQUIRED_SECTIONS:
        if sec not in document:
            errors.append(f"{aid}: missing required template section {sec!r}")

    # 5. Prohibited-language screen over our generated document + narrative. Strip the customer's
    #    own quoted words first — a customer disclosing "I was diagnosed with X" is legitimate
    #    input, never our prohibited assertion. We screen what the skill produces, not the customer.
    scan = document + " " + str(doc.get("narrative", ""))
    for s in signals:
        q = str(s.get("quote") or "").strip()
        if q:
            scan = scan.replace(q, " ")
    for pat in DIAGNOSTIC_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited diagnostic language detected: {m.group(0)!r} "
                          "(a signal is support context, never a diagnosis)")
    for pat in DISCRIMINATORY_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited discriminatory / capacity-determination language detected: "
                          f"{m.group(0)!r}")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice language detected: {m.group(0)!r} "
                          "(signpost to a licensed professional instead)")

    # 6. No autonomous system-of-record change.
    ru = doc.get("record_update") or {}
    if ru.get("applied") is not False or ru.get("mode") != "proposed":
        errors.append(f"{aid}: system-of-record change is not permitted — record_update must be "
                      "mode 'proposed' and applied false (marker/accommodation is a proposal)")

    # 7. External-delivery approval gate.
    if doc.get("human_review_required") is not True:
        errors.append(f"{aid}: draft not marked human_review_required (external-delivery approval gate)")

    # 8. Standing note present.
    if STANDING_NOTE.lower() not in (document + " " + str(doc.get("standing_note", ""))).lower():
        errors.append("missing standing note")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessment_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
