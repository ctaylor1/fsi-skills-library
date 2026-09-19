#!/usr/bin/env python3
"""Bundle canonical payment contracts in current payment packages; --check checks drift."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def targets():
    packages = sorted(p.parent for p in (ROOT / "skills/payments").glob("*/SKILL.md"))
    pci = ROOT / "skills/cybersecurity-operational-resilience/pci-dss-evidence-assistant"
    if (pci / "SKILL.md").exists():
        packages.append(pci)
    return packages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failures = []
    for package in targets():
        for source, destination in (
            ("payment_contract.py", "scripts/payment_contract.py"),
            ("payment-contract.md", "references/payment-contract.md"),
        ):
            data = (ROOT / "shared/payments" / source).read_bytes()
            target = package / destination
            if args.check:
                if not target.exists() or target.read_bytes() != data:
                    failures.append(str(target.relative_to(ROOT)))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    if failures:
        print("Contract drift:\n" + "\n".join(failures))
        return 1
    print(f"Payment contracts {'verified' if args.check else 'bundled'} in {len(targets())} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
