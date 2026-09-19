#!/usr/bin/env python3
"""Bundle the canonical wealth evidence helper; --check verifies no drift."""
from pathlib import Path
import argparse

REPO = Path(__file__).resolve().parents[1]
PACKAGES = (
    "wealth-client-discovery-assistant", "household-wealth-data-reconciler",
    "wealth-onboarding-packager", "investment-risk-profile-reviewer",
    "investment-recommendation-evidence-reviewer", "senior-investor-protection-screener",
    "wealth-management-router",
)
P1_PACKAGES = (
    "household-financial-planning-assistant", "investment-policy-statement-builder",
    "retirement-income-scenario-modeler", "portfolio-construction-assistant",
    "portfolio-proposal-comparator", "portfolio-rebalancing-assistant",
    "tax-aware-investment-reviewer", "estate-wealth-transfer-reviewer",
    "protection-needs-reviewer", "wealth-performance-report-builder",
    "wealth-account-service-packager", "advisory-fee-reviewer",
)
P2_PACKAGES = (
    "advisor-book-of-business-reviewer", "wealth-prospect-referral-preparer",
    "wealth-lending-liquidity-reviewer", "private-market-client-reviewer",
)
P3_PACKAGES = ("family-wealth-governance-preparer", "trust-administration-reviewer")
WORKFLOW_PACKAGES = P2_PACKAGES + P3_PACKAGES
PACKAGE_PATHS = tuple("wealth-management/" + name for name in PACKAGES + P1_PACKAGES + P2_PACKAGES + P3_PACKAGES) + (
    "asset-management/investment-manager-due-diligence-reviewer",
)
ANALYSIS_PACKAGES = ("tax-aware-investment-reviewer", "advisory-fee-reviewer", "wealth-performance-report-builder")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = (REPO / "shared/wealth-management/wealth_contract.py").read_bytes()
    failures = []
    for name in PACKAGE_PATHS:
        target = REPO / "skills" / name / "scripts/wealth_contract.py"
        if args.check:
            if not target.exists() or target.read_bytes() != data:
                failures.append(name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    analysis = (REPO / "shared/wealth-management/wealth_analysis.py").read_bytes()
    for name in ANALYSIS_PACKAGES:
        target = REPO / "skills/wealth-management" / name / "scripts/wealth_analysis.py"
        if args.check:
            if not target.exists() or target.read_bytes() != analysis:
                failures.append(name + "/wealth_analysis.py")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(analysis)
    workflow = (REPO / "shared/wealth-management/wealth_workflow.py").read_bytes()
    for name in WORKFLOW_PACKAGES:
        target = REPO / "skills/wealth-management" / name / "scripts/wealth_workflow.py"
        if args.check:
            if not target.exists() or target.read_bytes() != workflow:
                failures.append(name + "/wealth_workflow.py")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(workflow)
    if failures:
        print("Shared contract missing or changed: " + ", ".join(failures))
        return 1
    print(f"Wealth contract {'verified' if args.check else 'bundled'} in {len(PACKAGE_PATHS)} packages; analysis helpers in {len(ANALYSIS_PACKAGES)}; workflow helpers in {len(WORKFLOW_PACKAGES)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
