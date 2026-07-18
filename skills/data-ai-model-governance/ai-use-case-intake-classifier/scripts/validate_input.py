#!/usr/bin/env python3
"""Deterministic input validation for ai-use-case-intake-classifier.

Validates an AI use-case intake submission before factor classification. Fails closed on
structural problems; warns on data-quality gaps that limit which factors are evaluable.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  use_case_id, title, as_of (YYYY-MM-DD), config_version, purpose,
  user_populations[] (internal|customer|public), autonomy, decision_effect, model_type,
  external_provider(bool), data{personal_data(bool),special_category(bool),
  data_classification,affected_individuals}, materiality{financial_exposure_usd,
  affected_individuals}, jurisdictions[], prohibited_practice_indicators[], config{...}

Usage:
  python validate_input.py intake.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = (
    "use_case_id", "title", "as_of", "config_version", "purpose",
    "user_populations", "autonomy", "decision_effect", "model_type",
    "data", "jurisdictions",
)
AUTONOMY = {"informational", "recommendation", "decision-support", "autonomous-action"}
DECISION_EFFECT = {"none", "operational", "customer-impacting", "regulated-decision"}
MODEL_TYPE = {"rules", "classical-ml", "genai-llm", "agentic"}
POPULATIONS = {"internal", "customer", "public"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if doc["autonomy"] not in AUTONOMY:
        errors.append(f"autonomy must be one of {sorted(AUTONOMY)}, got {doc['autonomy']!r}")
    if doc["decision_effect"] not in DECISION_EFFECT:
        errors.append(f"decision_effect must be one of {sorted(DECISION_EFFECT)}, got {doc['decision_effect']!r}")
    if doc["model_type"] not in MODEL_TYPE:
        errors.append(f"model_type must be one of {sorted(MODEL_TYPE)}, got {doc['model_type']!r}")

    pops = doc.get("user_populations")
    if not isinstance(pops, list) or not pops:
        errors.append("user_populations must be a non-empty list")
    else:
        for p in pops:
            if p not in POPULATIONS:
                errors.append(f"user_populations value {p!r} not in {sorted(POPULATIONS)}")

    juris = doc.get("jurisdictions")
    if not isinstance(juris, list) or not juris:
        errors.append("jurisdictions must be a non-empty list")

    data = doc.get("data")
    if not isinstance(data, dict):
        errors.append("data must be an object")
    else:
        if "personal_data" in data and not isinstance(data["personal_data"], bool):
            errors.append("data.personal_data must be a boolean")
        if "special_category" in data and not isinstance(data["special_category"], bool):
            errors.append("data.special_category must be a boolean")
        if "affected_individuals" in data and _num(data["affected_individuals"]) is None:
            errors.append("data.affected_individuals must be numeric")

    if "external_provider" in doc and not isinstance(doc["external_provider"], bool):
        errors.append("external_provider must be a boolean")

    ppi = doc.get("prohibited_practice_indicators", [])
    if ppi and not isinstance(ppi, list):
        errors.append("prohibited_practice_indicators must be a list when present")

    if errors:
        return errors, warnings

    # data-quality warnings (limit which factors are evaluable) --------------------------
    if not doc.get("materiality"):
        warnings.append("no 'materiality' block — high_materiality is not evaluable")
    if data.get("personal_data") and data.get("affected_individuals") is None:
        warnings.append("personal_data is true but affected_individuals missing — personal_data_at_scale not evaluable")
    if "special_category" not in data:
        warnings.append("data.special_category absent — treated as false; confirm against the data catalog")
    if "external_provider" not in doc:
        warnings.append("external_provider absent — treated as false; confirm the provider")
    if not doc.get("config"):
        warnings.append("no 'config' block — default thresholds will be used; record the config_version")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "intake_example.json"
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
