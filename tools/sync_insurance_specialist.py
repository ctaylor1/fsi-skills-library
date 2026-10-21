#!/usr/bin/env python3
"""Bundle Phase 5 specialist dependencies without changing earlier runtimes."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pairs():
    manifest = json.loads((ROOT / "catalog/insurance-phase5-capabilities.json").read_text())
    for relative in manifest["all_native_packages"].values():
        package = ROOT / relative
        for name in ("workflow_contract.py", "workflow_foundation.py", "design_support.py"):
            yield ROOT / "shared/workflow-review" / name, package / "scripts" / name
        for name in ("workflow-contract.md", "workflow-foundation.md"):
            yield ROOT / "shared/workflow-review" / name, package / "references" / name
        yield ROOT / "shared/insurance/insurance_contract.py", package / "scripts/insurance_contract.py"
        yield ROOT / "shared/insurance/insurance-contract.md", package / "references/insurance-contract.md"
        yield ROOT / "shared/insurance-specialist/specialist_support.py", package / "scripts/specialist_support.py"
        yield ROOT / "shared/insurance-specialist/specialist-profile.md", package / "references/specialist-profile.md"


def check():
    return [
        str(target.relative_to(ROOT))
        for source, target in pairs()
        if not target.is_file() or source.read_bytes() != target.read_bytes()
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        for source, target in pairs():
            target.write_bytes(source.read_bytes())
    errors = check()
    print(f"Insurance specialist resources: {len(list(pairs()))} bundles; {len(errors)} missing/drifted")
    for error in errors:
        print(error)
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
