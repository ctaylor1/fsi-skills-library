#!/usr/bin/env python3
"""Deterministic, explainable subrogation-recovery screening for subrogation-opportunity-screener.

Reads a claim file (see validate_input.py), computes the configured recovery signals, attaches
evidence + citations to each, computes the referral economics, and maps the fired-signal set to
a screening band (Refer / Review / No-Action). Emits a machine-readable core the SKILL wraps in
a plain-language, source-linked referral for a licensed recovery/subrogation specialist.

IMPORTANT: This produces explainable *recovery signals and a triage suggestion* only. It never
makes a subrogation determination, a liability finding, or a limitation (time-bar) determination,
and it never issues a demand, files, waives, or takes any recovery action. The band mapping is
deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py claim.json | --selftest
Prints the screening JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "referral_floor": 2500.0, "min_liability_pct": 50.0, "recovery_cost_estimate": 750.0,
    "min_expected_net": 0.0, "limitation_buffer_days": 30, "limitation_urgent_days": 90,
    "collectibility_insured": 1.0, "collectibility_assets": 0.6, "collectibility_unknown": 0.3,
    "strong_evidence_types": ["police_report", "liability_admission", "expert_report"],
}
DISCLAIMER = ("Screening evidence only; not a subrogation, liability, or limitation "
              "determination. No demand, filing, waiver, or recovery action has been taken.")
CORE = {"third_party_liability_indicated", "recovery_above_floor", "positive_expected_recovery"}


def _parse_date(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def screening_band(fired: set, time_critical: bool) -> str:
    """Deterministic band from the fired-signal set (+ time-critical flag).

    Mirrored in validate_output.py; documented in references/domain-rules.md.
    """
    if "recovery_not_waived" not in fired:
        return "No-Action"  # already waived / handled — nothing to refer
    if CORE <= fired and "supporting_evidence_present" in fired and "limitation_window_open" in fired:
        band = "Refer"
    elif CORE <= fired:
        band = "Review"  # recovery value exists but an evidence/limitation/collectibility gap remains
    elif {"third_party_liability_indicated", "recovery_above_floor"} & fired:
        band = "Review"
    else:
        band = "No-Action"
    # Never let a live limitation window lapse silently: force human eyes.
    if band == "No-Action" and time_critical and "third_party_liability_indicated" in fired:
        band = "Review"
    return band


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    claim_id = doc["claim_id"]
    as_of = _parse_date(doc["as_of"])

    def cite(kind, ref=None):
        return f"claims:{ref or claim_id + ';' + kind}@{doc['as_of']}"

    signals, not_evaluable = [], []

    def add(name, fired, reason, evidence, basis, contribution):
        signals.append({"signal": name, "fired": bool(fired), "reason": reason,
                        "evidence": evidence, "basis": basis, "contribution": contribution})

    # --- financials ---
    paid = _num(doc.get("paid_to_date"))
    deductible = _num(doc.get("recovery_deductible"))
    net_incurred = _num(doc.get("net_incurred"), paid)
    recovery_base = paid + deductible
    fin_ref = doc.get("financials_source_ref", f"{claim_id};financials")

    # --- responsible parties / liability ---
    liab = doc.get("liability") or {}
    parties = liab.get("responsible_parties") or []
    qualifying = [p for p in parties if _num(p.get("liability_pct")) >= cfg["min_liability_pct"]]
    best = max(qualifying or parties, key=lambda p: _num(p.get("liability_pct")), default=None)

    # --- collectibility factor (from best responsible party) ---
    if best is not None:
        insured = bool(best.get("insured"))
        assets = bool(best.get("assets_known"))
        factor = (cfg["collectibility_insured"] if insured
                  else cfg["collectibility_assets"] if assets else cfg["collectibility_unknown"])
    else:
        insured = assets = False
        factor = cfg["collectibility_unknown"]

    liability_share = (_num(best.get("liability_pct")) / 100.0) if (best is not None and qualifying) else 0.0
    gross_expected = round(recovery_base * liability_share * factor, 2)
    net_expected = round(gross_expected - cfg["recovery_cost_estimate"], 2)

    # 1) third_party_liability_indicated
    add("third_party_liability_indicated", bool(liab.get("indicated")) and bool(qualifying),
        f"claim facts indicate a responsible third party with liability share >= {cfg['min_liability_pct']}%"
        if qualifying else "no responsible party at or above the liability-share floor",
        [{"party": p.get("name"), "role": p.get("role"), "liability_pct": _num(p.get("liability_pct")),
          "citation": cite("party", p.get("source_ref"))} for p in qualifying],
        {"basis": liab.get("basis"), "min_liability_pct": cfg["min_liability_pct"]}, len(qualifying))
    if not parties:
        not_evaluable.append({"signal": "third_party_liability_indicated",
                              "why": "no responsible_parties on file — liability not evaluable"})

    # 2) recovery_above_floor
    add("recovery_above_floor", recovery_base >= cfg["referral_floor"],
        f"recoverable base {recovery_base:.2f} (paid {paid:.2f} + deductible {deductible:.2f}) "
        f">= referral floor {cfg['referral_floor']:.2f}"
        if recovery_base >= cfg["referral_floor"]
        else f"recoverable base {recovery_base:.2f} below referral floor {cfg['referral_floor']:.2f}",
        [{"recovery_base": recovery_base, "net_incurred": net_incurred, "citation": cite("financials", fin_ref)}],
        {"referral_floor": cfg["referral_floor"]}, 1 if recovery_base >= cfg["referral_floor"] else 0)

    # 3) limitation_window_open
    lim_raw = doc.get("limitation_date")
    days_to_limitation = None
    if lim_raw:
        days_to_limitation = (_parse_date(lim_raw) - as_of).days
        open_ = days_to_limitation >= cfg["limitation_buffer_days"]
        add("limitation_window_open", open_,
            f"{days_to_limitation} day(s) to limitation date {lim_raw} (buffer {cfg['limitation_buffer_days']}d)",
            [{"limitation_date": str(lim_raw), "days_to_limitation": days_to_limitation,
              "citation": cite("limitation", doc.get("limitation_source_ref"))}] if open_ else [],
            {"limitation_buffer_days": cfg["limitation_buffer_days"]}, 1 if open_ else 0)
    else:
        not_evaluable.append({"signal": "limitation_window_open",
                              "why": "no limitation_date on file — resolve the controlling date before relying on the screen"})

    time_critical = days_to_limitation is not None and days_to_limitation <= cfg["limitation_urgent_days"]

    # 4) supporting_evidence_present
    strong = [e for e in (doc.get("evidence") or [])
              if e.get("present") and e.get("type") in set(cfg["strong_evidence_types"])]
    add("supporting_evidence_present", bool(strong),
        "strong liability evidence on file (" + ", ".join(sorted({e["type"] for e in strong})) + ")"
        if strong else "no strong liability evidence (police report / liability admission / expert report) on file",
        [{"type": e["type"], "citation": cite("evidence", e.get("source_ref"))} for e in strong],
        {"strong_evidence_types": cfg["strong_evidence_types"]}, len(strong))
    if not (doc.get("evidence")):
        not_evaluable.append({"signal": "supporting_evidence_present",
                              "why": "no evidence inventory on file — evidence completeness not evaluable"})

    # 5) recovery_not_waived (fires = recovery is still available to pursue)
    waived = bool(doc.get("waiver_of_subrogation"))
    prior_status = ((doc.get("prior_recovery") or {}).get("status") or "none")
    available = (not waived) and prior_status == "none"
    add("recovery_not_waived", available,
        "no waiver of subrogation and no prior/open recovery — recovery is available"
        if available else f"recovery unavailable (waiver={waived}, prior_recovery_status={prior_status})",
        [{"waiver_of_subrogation": waived, "prior_recovery_status": prior_status,
          "citation": cite("recovery-status", doc.get("recovery_status_source_ref"))}] if available else [],
        {"waiver_of_subrogation": waived, "prior_recovery_status": prior_status}, 1 if available else 0)

    # 6) collectible_responsible_party
    add("collectible_responsible_party", (best is not None) and (insured or assets),
        f"responsible party is {'insured' if insured else 'has known assets'}" if (best is not None and (insured or assets))
        else "responsible-party collectibility unknown",
        [{"party": best.get("name"), "insured": insured, "assets_known": assets,
          "citation": cite("party", best.get("source_ref"))}] if (best is not None and (insured or assets)) else [],
        {"collectibility_factor": factor}, 1 if (best is not None and (insured or assets)) else 0)
    if best is None:
        not_evaluable.append({"signal": "collectible_responsible_party",
                              "why": "no responsible party — collectibility not evaluable"})

    # 7) positive_expected_recovery
    add("positive_expected_recovery", net_expected > cfg["min_expected_net"],
        f"net expected recovery {net_expected:.2f} > {cfg['min_expected_net']:.2f}"
        if net_expected > cfg["min_expected_net"]
        else f"net expected recovery {net_expected:.2f} not above {cfg['min_expected_net']:.2f}",
        [{"gross_expected": gross_expected, "net_expected": net_expected, "citation": cite("financials", fin_ref)}],
        {"liability_share": liability_share, "collectibility_factor": factor}, 1 if net_expected > cfg["min_expected_net"] else 0)

    fired = {s["signal"] for s in signals if s["fired"]}
    band = screening_band(fired, time_critical)

    consider = []
    if band != "No-Action":
        consider = [
            "comparative or contributory negligence may reduce the recoverable share",
            "the responsible party may be judgment-proof or under-insured (verify collectibility)",
            "an anti-subrogation rule or the made-whole doctrine may limit recovery",
            "the limitation period varies by jurisdiction and claim type — confirm the controlling date with the recovery specialist / counsel",
            "another insurer or party may already be pursuing recovery (avoid a duplicate demand)",
            "policy conditions (e.g., a waiver-of-subrogation endorsement) may bar recovery",
        ]

    return {
        "screening_id": f"sos-{claim_id}-{doc['as_of']}-0001",
        "claim_id": claim_id,
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "line_of_business": doc.get("line_of_business"),
        "context": {"loss_date": doc.get("loss_date"), "loss_state": doc.get("loss_state"),
                    "limitation_date": lim_raw, "days_to_limitation": days_to_limitation},
        "time_critical": time_critical,
        "signals": signals,
        "fired_signals": sorted(fired),
        "not_evaluable": not_evaluable,
        "referral_economics": {
            "recovery_base": recovery_base, "liability_share": liability_share,
            "collectibility_factor": factor, "gross_expected": gross_expected,
            "recovery_cost": cfg["recovery_cost_estimate"], "net_expected": net_expected},
        "screening_band": band,
        "consider_prompts": consider,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
