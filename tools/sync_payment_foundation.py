#!/usr/bin/env python3
"""Bundle additive payment helpers and bounded public profiles in standalone skills."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    "bank-payment-workflow-designer", "payment-initiation-control-reviewer",
    "payment-regulatory-applicability-reviewer", "merchant-acceptance-strategy-designer",
    "card-program-designer", "card-lifecycle-operations-assistant",
    "payment-economics-modeler", "payment-servicing-planner",
    "payment-platform-architecture-reviewer", "payment-provider-evaluator",
)
PHASE3_PACKAGES = (
    "payment-acceptance-performance-analyzer", "payment-fraud-control-evaluator",
    "payment-credential-authentication-reviewer", "platform-payment-flow-designer",
    "commercial-payment-workflow-designer", "payment-liquidity-and-funding-analyzer",
    "payment-service-incident-investigator", "payment-operations-improvement-analyzer",
)
PHASE4_PACKAGES = (
    "cross-border-payment-designer", "wallet-and-mobile-money-program-designer",
    "stablecoin-settlement-assessor", "payment-business-model-analyzer",
)
AGENT_MODULES = (
    "payment-initiation-control-reviewer", "payment-credential-authentication-reviewer",
    "platform-payment-flow-designer",
)
RESOURCES = {
    "payment_foundation.py": "scripts/payment_foundation.py",
    "payment_contract.py": "scripts/payment_contract.py",
    "payment-contract.md": "references/payment-contract.md",
    "rail-profiles.json": "references/rail-profiles.json",
    "consumer-error-profiles.json": "references/consumer-error-profiles.json",
    "scheme-stage-profiles.json": "references/scheme-stage-profiles.json",
}


def sync(check=False):
    failures = []
    for name in PACKAGES + PHASE3_PACKAGES + PHASE4_PACKAGES + ("payment-integration-readiness-reviewer",):
        package = ROOT / "skills/payments" / name
        resources = dict(RESOURCES)
        if name == "bank-payment-workflow-designer":
            resources.update({"payment_messages.py": "scripts/payment_messages.py", "message-contracts.json": "references/message-contracts.json"})
        if name in ("bank-payment-workflow-designer", "cross-border-payment-designer"):
            resources["regional-profiles.json"] = "references/regional-profiles.json"
        if name in AGENT_MODULES:
            resources.update({"agent_commerce.py": "scripts/agent_commerce.py",
                              "agent-commerce-schema.md": "references/agent-commerce-schema.md",
                              "agent-commerce-protocols.md": "references/agent-commerce-protocols.md"})
        for source, target in resources.items():
            src, dst = ROOT / "shared/payments" / source, package / target
            if check:
                if not dst.exists() or src.read_bytes() != dst.read_bytes():
                    failures.append(str(dst.relative_to(ROOT)))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
    for name in ("issuer-payment-dispute-reviewer", "merchant-chargeback-response-packager"):
        for source, target in {
            "dispute_profiles.py": "scripts/dispute_profiles.py",
            "payment_foundation.py": "scripts/payment_foundation.py",
            "consumer-error-profiles.json": "references/consumer-error-profiles.json",
            "scheme-stage-profiles.json": "references/scheme-stage-profiles.json",
        }.items():
            src, dst = ROOT / "shared/payments" / source, ROOT / "skills/payments" / name / target
            if check:
                if not dst.exists() or src.read_bytes() != dst.read_bytes():
                    failures.append(str(dst.relative_to(ROOT)))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    errors = sync(args.check)
    for error in errors:
        print("DRIFT", error)
    print(f"Payment foundation: {len(PACKAGES) + len(PHASE3_PACKAGES) + len(PHASE4_PACKAGES) + 1} core packages plus 2 dispute extensions, {len(errors)} drift errors")
    raise SystemExit(bool(errors))
