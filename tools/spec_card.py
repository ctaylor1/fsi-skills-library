#!/usr/bin/env python3
"""Emit the exact SKILL.md frontmatter + a build "spec card" for a skill.

Derives every metadata value deterministically from catalog/skills-catalog.json so all 173
packages are consistent. The build workflow runs this per skill and pastes the frontmatter
verbatim.

Usage:
    python tools/spec_card.py <skill-name>
    python tools/spec_card.py <skill-name> --frontmatter-only
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECERT = "2027-07-17"
VERSION = "0.1.0"

CATEGORY_SLUG = {
    "Banking": "banking", "Capital Markets": "capital-markets", "Insurance": "insurance",
    "Payments": "payments", "Investment Banking & Research": "investment-banking-research",
    "Wealth Management": "wealth-management", "Asset Management": "asset-management",
    "Risk Management": "risk-management", "Compliance & Financial Crime": "compliance-financial-crime",
    "Finance & Operations": "finance-operations",
    "Cybersecurity & Operational Resilience": "cybersecurity-operational-resilience",
    "Customer Service & Experience": "customer-service-experience",
    "Data, AI & Model Governance": "data-ai-model-governance",
    "Enterprise Functions & Technology": "enterprise-functions-technology",
}
OWNER = {
    "Banking": "Banking product & credit operations",
    "Capital Markets": "Capital Markets operations & compliance",
    "Insurance": "Insurance underwriting & claims",
    "Payments": "Payments operations & risk",
    "Investment Banking & Research": "Investment Banking / Research",
    "Wealth Management": "Wealth Management advisory & compliance",
    "Asset Management": "Asset Management investment & product",
    "Risk Management": "Enterprise Risk Management",
    "Compliance & Financial Crime": "Compliance & Financial Crime (FIU)",
    "Finance & Operations": "Finance & Controllership",
    "Cybersecurity & Operational Resilience": "CISO / Operational Resilience",
    "Customer Service & Experience": "Customer Service & Experience",
    "Data, AI & Model Governance": "AI / Model Risk Governance",
    "Enterprise Functions & Technology": "Enterprise Functions & Technology",
}
DATA_CLASS = {
    "Banking": "Highly Confidential (customer NPI/PII)",
    "Capital Markets": "Highly Confidential (customer NPI/PII)",
    "Insurance": "Highly Confidential (customer NPI/PII)",
    "Payments": "Highly Confidential (customer NPI/PII; cardholder data)",
    "Investment Banking & Research": "Highly Confidential (MNPI / client-confidential)",
    "Wealth Management": "Highly Confidential (customer NPI/PII)",
    "Asset Management": "Highly Confidential (MNPI / client-confidential)",
    "Risk Management": "Confidential",
    "Compliance & Financial Crime": "Restricted (AML/BSA — SAR confidentiality; tipping-off controls)",
    "Finance & Operations": "Confidential (financial records)",
    "Cybersecurity & Operational Resilience": "Confidential (security-sensitive)",
    "Customer Service & Experience": "Highly Confidential (customer NPI/PII)",
    "Data, AI & Model Governance": "Confidential",
    "Enterprise Functions & Technology": "Confidential",
}
MIRROR = {
    "Explain & summarize": "skills/capital-markets/portfolio-holdings-summarizer",
    "Analyze & review": "skills/banking/account-anomaly-screener",
    "Investigate & casework": "skills/compliance-financial-crime/aml-alert-triager",
    "Orchestrate & resolve": "skills/banking/loan-servicing-exception-resolver",
    "Model & calculate": "skills/banking/account-anomaly-screener",
    "Reconcile & validate": "skills/banking/account-anomaly-screener",
    "Draft & package": "skills/compliance-financial-crime/aml-alert-triager",
    "Domain workflow": "skills/banking/account-anomaly-screener",
    "Monitor & alert": "skills/banking/account-anomaly-screener",
}
JURISDICTIONS = "US (default); configure additional jurisdiction packs per deployment"


def _short_tier(t: str) -> str:
    return t.split(" ")[0].strip() if t else ""


def _baseline(status: str) -> str:
    return {"existing (no changes)": "existing-no-changes",
            "existing (updated)": "existing-updated", "new": "new"}.get(status, "new")


def _scheduled(v: str) -> str:
    return "read-only-monitoring" if v.lower().startswith("yes") else "no"


def _approval(tier: str) -> str:
    return "required" if tier in ("R3", "R4") else "external-delivery"


def _ascii(v: str) -> str:
    return v.replace("—", "-").replace("–", "-") if v else v


def card(s: dict) -> tuple[str, str]:
    tier = _short_tier(s["risk_tier"])
    slug = CATEGORY_SLUG[s["category"]]
    wave = _ascii(s["delivery_wave"])
    fm = f'''metadata:
  aws-fsi-category: "{s['category']}"
  aws-fsi-skill-type: "{s['skill_type']}"
  aws-fsi-risk-tier: "{tier}"
  aws-fsi-archetype: "{s['archetype']}"
  aws-fsi-agent-pattern: "{s['agent_pattern']}"
  aws-fsi-delivery-wave: "{wave}"
  aws-fsi-action-mode: "{s['action_mode']}"
  aws-fsi-scheduled-agent: "{_scheduled(s['scheduled_agent'])}"
  aws-fsi-baseline-status: "{_baseline(s['status'])}"
  aws-fsi-human-approval: "{_approval(tier)}"
  aws-fsi-data-classification: "{DATA_CLASS[s['category']]}"
  aws-fsi-jurisdictions: "{JURISDICTIONS}"
  aws-fsi-owner: "{OWNER[s['category']]}"
  aws-fsi-primary-user: "{s['primary_user']}"
  aws-fsi-version: "{VERSION}"
  aws-fsi-recertification-date: "{RECERT}"'''

    info = f'''# Build spec card — {s['name']}

directory:        skills/{slug}/{s['name']}/
category:         {s['category']}
skill_type:       {s['skill_type']}
risk_tier:        {s['risk_tier']}
archetype:        {s['archetype']}
agent_pattern:    {s['agent_pattern']}
delivery_wave:    {s['delivery_wave']}
action_mode:      {s['action_mode']}
human_approval:   {_approval(tier)}
scheduled_agent:  {_scheduled(s['scheduled_agent'])}
baseline_status:  {_baseline(s['status'])}
primary_user:     {s['primary_user']}
mirror_exemplar:  {MIRROR.get(s['archetype'], MIRROR['Analyze & review'])}

catalog_description (expand into a spec-quality what+when+boundary description):
  {s['description']}

minimum_tooling_data:
  {s['tooling_data']}

primary_validation_focus:
  {s['validation_focus']}
'''
    return fm, info


def main(argv):
    if not argv:
        print("usage: spec_card.py <skill-name> [--frontmatter-only]", file=sys.stderr)
        return 2
    name = argv[0]
    cat = json.loads((REPO / "catalog" / "skills-catalog.json").read_text(encoding="utf-8"))
    s = next((x for x in cat["skills"] if x["name"] == name), None)
    if not s:
        print(f"ERROR: skill {name!r} not in catalog", file=sys.stderr)
        return 1
    fm, info = card(s)
    if "--frontmatter-only" in argv:
        print(fm)
    else:
        print(info)
        print("\n--- frontmatter metadata block ---\n")
        print(fm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
