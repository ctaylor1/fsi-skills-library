#!/usr/bin/env python3
"""Bundle insurance contract reference everywhere; helper only in importing packages."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def targets():
    return sorted(p.parent for p in (ROOT / "skills/insurance").glob("*/SKILL.md"))


def needs_helper(package):
    return any("import insurance_contract" in p.read_text() or "from insurance_contract import" in p.read_text()
               for p in (package / "scripts").glob("*.py") if p.name != "insurance_contract.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failures, copies = [], 0
    for package in targets():
        pairs = [("insurance-contract.md", "references/insurance-contract.md")]
        if needs_helper(package):
            pairs.append(("insurance_contract.py", "scripts/insurance_contract.py"))
            copies += 1
        for source, relative in pairs:
            data = (ROOT / "shared/insurance" / source).read_bytes()
            dest = package / relative
            if args.check:
                if not dest.exists() or dest.read_bytes() != data:
                    failures.append(str(dest.relative_to(ROOT)))
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
    if failures:
        print("Contract drift:\n" + "\n".join(failures))
        return 1
    print(f"Insurance contract {'verified' if args.check else 'bundled'}: {len(targets())} references, {copies} helpers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
