#!/usr/bin/env python3
"""Deterministic, explainable intake classification for ai-use-case-intake-classifier.

Reads an AI use-case intake submission (see validate_input.py), evaluates the configured risk
factors, attaches evidence + citations to each fired factor, maps the fired-factor set to a
governance tier and a recommended governance path, and derives the required review gates. Emits a
machine-readable core the SKILL wraps in a plain-language classification record.

IMPORTANT: This produces an explainable *classification and a governance-routing recommendation*
only. It never approves, clears, exempts, waives, or closes a use case, and never makes the binding
governance decision. The tier/path mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py intake.json | --selftest
Prints the classification JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "personal_data_scale_threshold": 10000,
    "high_materiality_exposure_usd": 1000000,
    "high_materiality_individuals": 100000,
    "restricted_jurisdictions": ["EU", "UK", "CN"],
}
DISCLAIMER = ("Provisional classification prepared for human governance adjudication only; it does "
              "not grant, waive, exempt, or close any governance review, and is not a deployment "
              "authorization.")

HIGH_TRIGGERS = {"regulated_decision", "autonomous_action", "special_category_data", "high_materiality"}

PATH_BY_TIER = {
    "Prohibited": "Prohibited-practice escalation - route to Legal/Ethics; do not proceed pending human adjudication",
    "High": "Full governance review",
    "Limited": "Standard governance review",
    "Minimal": "Lightweight review (register and attest)",
}

REVIEWS_BY_FACTOR = {
    "regulated_decision": ["Legal/Compliance regulated-decision review", "Model risk validation"],
    "autonomous_action": ["Agent permission-scope and human-in-the-loop review"],
    "customer_or_public_facing": ["Fairness and conduct review"],
    "special_category_data": ["Privacy / DPIA review"],
    "personal_data_at_scale": ["Privacy / DPIA review"],
    "high_materiality": ["Senior management approval gate"],
    "cross_border": ["Cross-jurisdiction legal review"],
    "third_party_model": ["Third-party AI due diligence"],
    "genai_or_agentic": ["Prompt and agent risk review", "Evaluation benchmark"],
    "prohibited_practice_flag": ["Legal/Ethics prohibited-practice escalation"],
}


def _cite(doc: dict, field: str) -> str:
    return f"intake:{doc['use_case_id']};field={field}@{doc['as_of']}"


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def expected_tier(fired: list[str]) -> str:
    """Deterministic tier mapping (see references/domain-rules.md). First match wins."""
    f = set(fired)
    if "prohibited_practice_flag" in f:
        return "Prohibited"
    if (HIGH_TRIGGERS & f) or len(f) >= 3:
        return "High"
    if len(f) >= 1:
        return "Limited"
    return "Minimal"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    data = doc.get("data") or {}
    materiality = doc.get("materiality") or {}
    jurisdictions = [str(j).upper() for j in (doc.get("jurisdictions") or [])]
    restricted = {str(j).upper() for j in cfg.get("restricted_jurisdictions", [])}
    pops = [str(p) for p in (doc.get("user_populations") or [])]

    factors, not_evaluable = [], []

    def add(name, fired, reason, evidence, weight=1):
        factors.append({"factor": name, "fired": bool(fired), "reason": reason,
                        "evidence": evidence, "weight": weight if fired else 0})

    # regulated_decision
    add("regulated_decision", doc.get("decision_effect") == "regulated-decision",
        "decision_effect is a regulated decision" if doc.get("decision_effect") == "regulated-decision"
        else f"decision_effect is {doc.get('decision_effect')!r}",
        [{"field": "decision_effect", "value": doc.get("decision_effect"), "citation": _cite(doc, "decision_effect")}]
        if doc.get("decision_effect") == "regulated-decision" else [])

    # autonomous_action
    add("autonomous_action", doc.get("autonomy") == "autonomous-action",
        "autonomy is autonomous-action (no human in the loop)" if doc.get("autonomy") == "autonomous-action"
        else f"autonomy is {doc.get('autonomy')!r}",
        [{"field": "autonomy", "value": doc.get("autonomy"), "citation": _cite(doc, "autonomy")}]
        if doc.get("autonomy") == "autonomous-action" else [])

    # customer_or_public_facing
    cpf = bool({"customer", "public"} & set(pops))
    add("customer_or_public_facing", cpf,
        f"user_populations includes {sorted({'customer','public'} & set(pops))}" if cpf else "internal users only",
        [{"field": "user_populations", "value": pops, "citation": _cite(doc, "user_populations")}] if cpf else [])

    # special_category_data
    scd = data.get("special_category") is True
    add("special_category_data", scd,
        "data includes special-category attributes" if scd else "no special-category data declared",
        [{"field": "data.special_category", "value": True, "citation": _cite(doc, "data.special_category")}] if scd else [])

    # personal_data_at_scale (not evaluable if personal_data true but count missing)
    if data.get("personal_data") is True and _num(data.get("affected_individuals")) is None:
        not_evaluable.append({"factor": "personal_data_at_scale", "why": "personal_data true but affected_individuals missing"})
    else:
        n = _num(data.get("affected_individuals")) or 0
        pdas = data.get("personal_data") is True and n >= cfg["personal_data_scale_threshold"]
        add("personal_data_at_scale", pdas,
            f"personal data on {int(n)} individuals >= threshold {cfg['personal_data_scale_threshold']}" if pdas
            else "personal data below scale threshold or not personal",
            [{"field": "data.affected_individuals", "value": int(n), "citation": _cite(doc, "data.affected_individuals")}] if pdas else [])

    # high_materiality (not evaluable if no materiality block)
    if not materiality:
        not_evaluable.append({"factor": "high_materiality", "why": "no materiality block"})
    else:
        exposure = _num(materiality.get("financial_exposure_usd")) or 0
        indiv = _num(materiality.get("affected_individuals")) or 0
        hm = exposure >= cfg["high_materiality_exposure_usd"] or indiv >= cfg["high_materiality_individuals"]
        ev = []
        if hm:
            if exposure >= cfg["high_materiality_exposure_usd"]:
                ev.append({"field": "materiality.financial_exposure_usd", "value": exposure, "citation": _cite(doc, "materiality.financial_exposure_usd")})
            if indiv >= cfg["high_materiality_individuals"]:
                ev.append({"field": "materiality.affected_individuals", "value": indiv, "citation": _cite(doc, "materiality.affected_individuals")})
        add("high_materiality", hm,
            f"exposure {exposure:.0f} or affected {indiv:.0f} meets a materiality threshold" if hm
            else "below materiality thresholds", ev)

    # cross_border
    xb_multi = len(set(jurisdictions)) > 1
    xb_restricted = bool(set(jurisdictions) & restricted)
    xb = xb_multi or xb_restricted
    add("cross_border", xb,
        (f"{len(set(jurisdictions))} jurisdictions" if xb_multi else "")
        + (" incl. restricted" if xb_restricted else "") if xb else "single, non-restricted jurisdiction",
        [{"field": "jurisdictions", "value": jurisdictions, "citation": _cite(doc, "jurisdictions")}] if xb else [])

    # third_party_model
    tpm = doc.get("external_provider") is True
    add("third_party_model", tpm,
        "external AI provider in use" if tpm else "no external provider declared",
        [{"field": "external_provider", "value": True, "citation": _cite(doc, "external_provider")}] if tpm else [])

    # genai_or_agentic
    ga = doc.get("model_type") in ("genai-llm", "agentic")
    add("genai_or_agentic", ga,
        f"model_type is {doc.get('model_type')}" if ga else f"model_type is {doc.get('model_type')!r}",
        [{"field": "model_type", "value": doc.get("model_type"), "citation": _cite(doc, "model_type")}] if ga else [])

    # prohibited_practice_flag
    ppi = doc.get("prohibited_practice_indicators") or []
    pp = bool(ppi)
    add("prohibited_practice_flag", pp,
        f"prohibited-practice indicator(s) present: {ppi}" if pp else "no prohibited-practice indicator",
        [{"field": "prohibited_practice_indicators", "value": ppi, "citation": _cite(doc, "prohibited_practice_indicators")}] if pp else [])

    fired_names = [s["factor"] for s in factors if s["fired"]]
    tier = expected_tier(fired_names)
    path = PATH_BY_TIER[tier]

    # required reviews (deterministic, deduped, sorted)
    reviews: list[str] = []
    for name in fired_names:
        reviews.extend(REVIEWS_BY_FACTOR.get(name, []))
    if not fired_names:
        reviews = ["Register in AI inventory and owner attestation"]
    required_reviews = sorted(set(reviews))

    open_questions = [ne["factor"] + ": " + ne["why"] for ne in not_evaluable]

    return {
        "classification_id": f"aic-{doc['use_case_id']}-{doc['as_of']}-0001",
        "use_case_id": doc["use_case_id"],
        "title": doc.get("title"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "factors": factors,
        "fired_factors": fired_names,
        "not_evaluable": not_evaluable,
        "open_questions": open_questions,
        "governance_tier": tier,
        "recommended_governance_path": path,
        "required_reviews": required_reviews,
        "human_adjudication_required": True,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
