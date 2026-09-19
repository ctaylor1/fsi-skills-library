"""Prepare source-backed, case-scoped profile inputs from a supplied specialist review.

No deadline is inferred and no reviewer identity is authenticated. Public reference
profiles alone remain drafts; case clocks and licensed scheme criteria are separate.
"""
from datetime import date
import json
from pathlib import Path

from payment_foundation import load_resource
from payment_contract import stable_hash


def prepare(doc):
    kind = doc.get("kind")
    if kind not in {"consumer-error", "scheme-stage"}:
        raise ValueError("kind must be consumer-error or scheme-stage")
    filename = "consumer-error-profiles.json" if kind == "consumer-error" else "scheme-stage-profiles.json"
    reference = load_resource(filename)["profiles"].get(doc.get("profile_id"))
    if reference is None:
        return {"status": "unsupported-profile", "authority_granted": False, "issues": ["No matching source-backed reference profile."]}
    current = date.fromisoformat(doc["as_of"])
    scope, review = doc.get("scope", {}), doc.get("review", {})
    if not isinstance(scope, dict) or not isinstance(review, dict):
        raise ValueError("scope and review must be objects")
    issues = []
    if not date.fromisoformat(reference["reviewed_on"]) <= current <= date.fromisoformat(reference["review_due"]):
        issues.append("Reference profile not available/current for requested as_of.")
    for key in ("case_id", "participant", "jurisdiction", "product", "rail"):
        if not scope.get(key):
            issues.append("Scope requires " + key)
    if kind == "consumer-error":
        for field, key in (("participant", "participants"), ("jurisdiction", "jurisdictions"), ("product", "products"), ("rail", "rails")):
            if scope.get(field) not in reference[key]:
                issues.append("Reference does not cover " + field)
    else:
        if scope.get("network") != reference["network"] or scope.get("stage") != reference["stage"] or scope.get("participant") != reference["lead_role"]:
            issues.append("Scheme network, stage and participant must match the reference.")
        # A public stage guide cannot become an active licensed rule/eligibility pack.
        issues.append("Stage orientation is not a licensed case rule pack; supply current authorized criteria and case notice to the native reviewer.")
    for key in ("owner", "source_ref", "applicability_rationale", "effective_from", "review_due"):
        if not review.get(key):
            issues.append("Specialist review requires " + key)
    if review.get("scope_hash") != stable_hash(scope):
        issues.append("Specialist review must bind the exact case/product/rail/jurisdiction scope.")
    try:
        if not date.fromisoformat(review["effective_from"]) <= current <= date.fromisoformat(review["review_due"]):
            issues.append("Specialist review is outside its effective interval.")
    except (KeyError, TypeError, ValueError):
        issues.append("Specialist review effective/review dates must be valid ISO dates.")
    names = review.get("required_clock_names", [])
    if kind == "consumer-error" and (not isinstance(names, list) or not names or any(n not in reference["required_clock_names"] for n in names) or len(names) != len(set(names))):
        issues.append("Reviewer must identify distinct applicable statutory clock names from the reference, considering its exceptions.")
    profile = {
        "profile_id": reference["profile_id"] + ":" + str(scope.get("case_id", "unknown")),
        "version": reference["version"], "status": "draft" if issues else "active",
        "source_ref": reference["source_ref"], "authority": reference.get("authority", "Card scheme; public stage orientation"),
        "review_owner": review.get("owner"), "review_ref": review.get("source_ref"),
        "effective_from": review.get("effective_from"), "review_due": review.get("review_due"),
        "participants": [scope.get("participant")], "jurisdictions": [scope.get("jurisdiction")],
        "products": [scope.get("product")], "rails": [scope.get("rail")],
        "regime": reference.get("regime"), "applicability_rationale": review.get("applicability_rationale"),
        "required_clock_names": names if isinstance(names, list) else [],
        "required_evidence_types": reference.get("required_evidence_types", []),
        "required_action_reviews": reference.get("required_action_reviews", []),
        "case_scope": scope, "case_scope_hash": stable_hash(scope),
    }
    return {"status": "needs-review" if issues else "supplied-profile-for-native-review", "profile": profile,
            "reference_profile": reference, "issues": issues, "authority_granted": False,
            "input_hash": stable_hash(doc), "deadlines_calculated": False,
            "next_step": "Supply independently reviewed trigger evidence, named calendars/cutoffs and due dates to the native issuer or merchant reviewer; this preparation does not establish their correctness."}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(json.loads(Path(args.path).read_text())), indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}))
        return 1
