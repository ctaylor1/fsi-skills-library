#!/usr/bin/env python3
"""Deterministic support-needs assessment builder for vulnerable-customer-support-assistant.

Reads a de-identified interaction record (see validate_input.py). For each cited signal the
customer actually said/wrote, it assigns a vulnerability DRIVER category (Health, Life events,
Resilience, Capability), selects the APPROVED accommodations whose applicable signal types match,
chooses a suggested referral route by the documented priority (safeguarding first), and records
consent + human-approval flags. It renders the approved output template so the SKILL can present
a cited, review-ready draft.

IMPORTANT: This produces *drafting support* only. It never diagnoses a condition, never
determines mental capacity, never limits service or frames a customer on a protected
characteristic, never gives financial/medical/legal advice, and never records a marker, applies
an accommodation, or contacts the customer. Every accommodation is drawn from the approved
catalog and traced to a cited signal (no unsupported/unapproved claim). The driver map,
accommodations catalog, and referral routes are documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py interaction.json | --selftest
Prints the assessment JSON to stdout. With --selftest it also prints a trailing
"calculate self-test: N error(s)" line (exit 0 pass / 1 fail) after an internal invariant check.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft support-needs suggestions for human review only; this is not a diagnosis and not a "
    "determination about the customer, it applies no vulnerability marker or accommodation to any "
    "system of record and sends nothing to the customer, and every suggestion is drawn from the "
    "approved catalog and must be confirmed with the customer and an authorized colleague before "
    "anything is applied."
)

DRIVERS = ("Health", "Life events", "Resilience", "Capability")

# signal_type -> {driver, sensitive, force_route}
SIGNAL_MAP = {
    "bereavement": {"driver": "Life events", "sensitive": False},
    "caring_responsibility": {"driver": "Life events", "sensitive": False},
    "income_shock_job_loss": {"driver": "Resilience", "sensitive": False},
    "financial_difficulty_arrears": {"driver": "Resilience", "sensitive": False},
    "serious_illness": {"driver": "Health", "sensitive": True},
    "disability_access_need": {"driver": "Health", "sensitive": False},
    "mental_health_disclosed": {"driver": "Health", "sensitive": True},
    "cognitive_or_memory_difficulty": {"driver": "Capability", "sensitive": True},
    "language_barrier": {"driver": "Capability", "sensitive": False},
    "low_product_understanding": {"driver": "Capability", "sensitive": False},
    "digital_exclusion": {"driver": "Capability", "sensitive": False},
    "domestic_or_economic_abuse": {"driver": "Life events", "sensitive": True, "force_route": "safeguarding-team"},
    "risk_of_harm": {"driver": "Health", "sensitive": True, "force_route": "safeguarding-team"},
}

# accommodation code -> {label, signal_types[], requires_consent}
ACCOMMODATIONS = {
    "ACC-COMMS-ALT": {"label": "Alternative communication format (large print, post, email)",
                      "signal_types": ["disability_access_need", "digital_exclusion", "low_product_understanding"],
                      "requires_consent": False},
    "ACC-EXTRA-TIME": {"label": "Allow extra time; avoid pressuring decisions",
                       "signal_types": ["bereavement", "serious_illness", "mental_health_disclosed",
                                        "cognitive_or_memory_difficulty", "caring_responsibility",
                                        "low_product_understanding"],
                       "requires_consent": False},
    "ACC-THIRD-PARTY": {"label": "Register a trusted third party / authorized representative",
                        "signal_types": ["cognitive_or_memory_difficulty", "disability_access_need",
                                         "serious_illness", "mental_health_disclosed", "caring_responsibility"],
                        "requires_consent": True},
    "ACC-INTERPRETER": {"label": "Arrange interpreter / translation",
                        "signal_types": ["language_barrier"], "requires_consent": False},
    "ACC-QUIET-CHANNEL": {"label": "Switch to the customer's preferred lower-stress channel",
                          "signal_types": ["mental_health_disclosed", "serious_illness", "disability_access_need"],
                          "requires_consent": False},
    "ACC-SPECIALIST-CALLBACK": {"label": "Offer a callback from a trained specialist",
                                "signal_types": ["mental_health_disclosed", "domestic_or_economic_abuse",
                                                 "risk_of_harm", "cognitive_or_memory_difficulty"],
                                "requires_consent": False},
    "ACC-FORBEARANCE-SIGNPOST": {"label": "Signpost the approved financial-difficulty / forbearance process",
                                 "signal_types": ["income_shock_job_loss", "financial_difficulty_arrears"],
                                 "requires_consent": False},
    "ACC-EXTERNAL-SUPPORT-SIGNPOST": {"label": "Signpost approved external support organizations",
                                      "signal_types": ["bereavement", "serious_illness", "mental_health_disclosed",
                                                       "domestic_or_economic_abuse", "caring_responsibility"],
                                      "requires_consent": False},
}

APPROVED_ROUTES = ["safeguarding-team", "internal-vulnerability-specialist",
                   "financial-difficulty-team", "external-support-signpost"]

REQUIRED_SECTIONS = [
    "Support-needs assessment (DRAFT)",
    "Observed signals",
    "Possible support needs",
    "Suggested accommodations",
    "Suggested referral",
    "Consent and approvals",
    "What this is not",
]


def _cite(sig):
    return f"transcript:{sig.get('source_ref', '?')}"


def _cfg(doc):
    cfg = doc.get("config") or {}
    return {
        "signal_map": {**SIGNAL_MAP, **(cfg.get("signal_map") or {})},
        "accommodations": {**ACCOMMODATIONS, **(cfg.get("accommodations") or {})},
        "routes": list(cfg.get("routes") or APPROVED_ROUTES),
    }


def _map_signals(signals, cfg):
    observed, drivers, sensitive_present, force_routes = [], [], False, []
    for i, sig in enumerate(signals):
        stype = str(sig.get("signal_type"))
        meta = cfg["signal_map"].get(stype)
        sid = sig.get("signal_id") or f"S{i+1}"
        row = {
            "signal_id": sid,
            "signal_type": stype,
            "quote": sig.get("quote"),
            "citation": _cite(sig),
            "driver": meta.get("driver") if meta else None,
            "sensitive": bool(meta.get("sensitive")) if meta else False,
            "recognized": meta is not None,
        }
        observed.append(row)
        if meta:
            if meta.get("driver") not in drivers:
                drivers.append(meta["driver"])
            if meta.get("sensitive"):
                sensitive_present = True
            if meta.get("force_route"):
                force_routes.append(meta["force_route"])
    return observed, drivers, sensitive_present, force_routes


def _accommodations(observed, cfg, consent_granted):
    by_type = {}
    for row in observed:
        by_type.setdefault(row["signal_type"], []).append(row["signal_id"])
    out = []
    for code, spec in cfg["accommodations"].items():
        supporting = sorted({sid for t in spec["signal_types"] for sid in by_type.get(t, [])})
        if not supporting:
            continue
        needs_consent = bool(spec.get("requires_consent"))
        status = "suggested"
        if needs_consent and not consent_granted:
            status = "pending_consent"
        out.append({
            "code": code,
            "label": spec["label"],
            "supporting_signals": supporting,
            "requires_consent": needs_consent,
            "status": status,
            "catalog_ref": f"config:vuln-support#{code}",
        })
    out.sort(key=lambda a: a["code"])
    return out


def _referral(observed, drivers, sensitive_present, force_routes, cfg):
    triggered = []
    if force_routes:
        triggered.append("safeguarding-team")
    if sensitive_present or len(drivers) >= 2:
        triggered.append("internal-vulnerability-specialist")
    if "Resilience" in drivers:
        triggered.append("financial-difficulty-team")
    if ("Health" in drivers or "Life events" in drivers):
        triggered.append("external-support-signpost")
    # keep only approved + preserve documented priority order, dedup
    order = [r for r in cfg["routes"] if r in triggered]
    seen, ordered = set(), []
    for r in order:
        if r not in seen:
            seen.add(r)
            ordered.append(r)
    if not ordered:
        return None, []
    primary = ordered[0]
    supporting = sorted({row["signal_id"] for row in observed if row["recognized"]})
    heightened = bool(force_routes)
    return {
        "route": primary,
        "reason": ("Disclosed abuse or risk of harm — route to safeguarding without delay."
                   if primary == "safeguarding-team" else
                   "Multiple or sensitive support signals — route to a trained specialist."
                   if primary == "internal-vulnerability-specialist" else
                   "Financial-resilience signal — route to the financial-difficulty support team."
                   if primary == "financial-difficulty-team" else
                   "Signpost approved external support organizations."),
        "supporting_signals": supporting,
        "heightened": heightened,
    }, ordered[1:]


def _render(doc):
    lines = []
    a = doc
    lines.append(f"# Support-needs assessment (DRAFT) — {a['customer_ref']}")
    lines.append("")
    lines.append(f"Reference: {a['assessment_id']} | Channel: {a.get('channel')} | "
                 f"Signals: {len(a['observed_signals'])} | Readiness: {a['readiness']}")
    lines.append("")
    lines.append("## Observed signals")
    if a["observed_signals"]:
        for s in a["observed_signals"]:
            lines.append(f"- [{s['signal_id']}] \"{s['quote']}\" — {s['driver']} "
                         f"({s['signal_type']}) — {s['citation']}")
    else:
        lines.append("- None identified from the provided context.")
    lines.append("")
    lines.append("## Possible support needs")
    if a["driver_summary"]:
        for drv, ids in a["driver_summary"].items():
            lines.append(f"- {drv}: signalled by {', '.join(ids)} (current context, not a diagnosis)")
    else:
        lines.append("- No support need identified from the provided context.")
    lines.append("")
    lines.append("## Suggested accommodations")
    if a["suggested_accommodations"]:
        for acc in a["suggested_accommodations"]:
            flag = " [pending_consent]" if acc["status"] == "pending_consent" else ""
            lines.append(f"- {acc['code']} — {acc['label']}{flag} "
                         f"(supports: {', '.join(acc['supporting_signals'])})")
    else:
        lines.append("- None suggested.")
    lines.append("")
    lines.append("## Suggested referral")
    if a["suggested_referral"]:
        r = a["suggested_referral"]
        extra = f"; additional: {', '.join(a['additional_routes'])}" if a["additional_routes"] else ""
        lines.append(f"- Primary route: {r['route']} — {r['reason']}{extra}")
    else:
        lines.append("- No referral suggested; accommodations may suffice — the human decides.")
    lines.append("")
    lines.append("## Consent and approvals")
    lines.append(f"- Special-category data involved: {a['consent']['special_category_data_involved']}; "
                 f"consent status: {a['consent']['customer_consent_status']}")
    lines.append(f"- Human review required before anything is shared, recorded, or referred: "
                 f"{a['human_review_required']}")
    lines.append(f"- System-of-record change: {a['record_update']['mode']} "
                 f"(applied: {a['record_update']['applied']})")
    lines.append("")
    lines.append("## What this is not")
    lines.append("- Not a diagnosis, not a capacity determination, not advice, and not a decision "
                 "to limit service. A human reviews and an authorized colleague acts.")
    lines.append("")
    lines.append(f"> {STANDING_NOTE}")
    return "\n".join(lines)


def build(doc: dict) -> dict:
    cfg = _cfg(doc)
    signals = doc.get("observed_signals") or []
    consent = doc.get("consent") or {}
    special = bool(consent.get("special_category_data_involved"))
    consent_status = str(consent.get("customer_consent_status", "not_captured"))
    consent_granted = consent_status == "granted"

    observed, drivers, sensitive_present, force_routes = _map_signals(signals, cfg)
    # sensitive signal in the interaction implies special-category data is involved
    special = special or sensitive_present

    accommodations = _accommodations(observed, cfg, consent_granted)
    referral, additional = _referral(observed, drivers, sensitive_present, force_routes, cfg)

    driver_summary = {}
    for drv in DRIVERS:
        ids = [row["signal_id"] for row in observed if row["driver"] == drv]
        if ids:
            driver_summary[drv] = ids

    needs = []
    for row in observed:
        if not row["recognized"]:
            needs.append(f"unrecognized signal_type {row['signal_type']!r} for {row['signal_id']}")
    if special and not consent_granted:
        needs.append("capture the customer's consent to record special-category data before "
                     "recording a marker or applying consent-dependent accommodations")
    readiness = "signals_mapped" if observed else "no_support_need_identified"

    cust = str(doc.get("customer_ref", "UNKNOWN"))
    assessment = {
        "assessment_id": f"vcs-{cust.replace('*', '')}-{doc.get('interaction_id', '0001')}",
        "config_version": doc.get("config_version"),
        "customer_ref": doc.get("customer_ref"),
        "channel": doc.get("channel"),
        "observed_signals": observed,
        "driver_summary": driver_summary,
        "suggested_accommodations": accommodations,
        "suggested_referral": referral,
        "additional_routes": additional,
        "consent": {
            "special_category_data_involved": special,
            "customer_consent_status": consent_status if special else "not_required",
        },
        "record_update": {"mode": "proposed", "applied": False},
        "human_review_required": True,
        "needs": needs,
        "readiness": readiness,
        "standing_note": STANDING_NOTE,
    }
    assessment["document"] = _render(assessment)
    return assessment


def _selftest_invariants(a: dict) -> list[str]:
    """Internal invariants: the builder must never emit an unapproved/unsupported suggestion."""
    errs = []
    for acc in a["suggested_accommodations"]:
        if acc["code"] not in ACCOMMODATIONS:
            errs.append(f"emitted unapproved accommodation {acc['code']}")
        if not acc["supporting_signals"]:
            errs.append(f"emitted unsupported accommodation {acc['code']}")
    if a["suggested_referral"] and a["suggested_referral"]["route"] not in APPROVED_ROUTES:
        errs.append("emitted unapproved referral route")
    for sec in REQUIRED_SECTIONS:
        if sec not in a["document"]:
            errs.append(f"rendered document missing section {sec!r}")
    if a["record_update"]["applied"] is not False:
        errs.append("record_update.applied must be False")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "interaction_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    result = build(doc)
    print(json.dumps(result, indent=2))
    if selftest:
        errs = _selftest_invariants(result)
        for e in errs:
            print("ERROR", e)
        print(f"calculate self-test: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
