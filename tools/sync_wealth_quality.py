#!/usr/bin/env python3
"""Bundle the scoped P5 quality controls; --check detects portable-copy drift."""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    "household-financial-planning-assistant", "investment-policy-statement-builder",
    "investment-recommendation-evidence-reviewer", "tax-aware-investment-reviewer",
    "estate-wealth-transfer-reviewer", "protection-needs-reviewer",
    "senior-investor-protection-screener",
    "client-review-preparer", "advisor-follow-up-assistant",
    "family-wealth-governance-preparer", "trust-administration-reviewer",
)
FILES = {
    "evidence_gate.py": "scripts/evidence_gate.py",
    "audience_gate.py": "scripts/audience_gate.py",
    "quality_gate.py": "scripts/quality_gate.py",
    "EVIDENCE-GATE.md": "references/evidence-gate.md",
    "AUDIENCE-GATE.md": "references/audience-gate.md",
    "QUALITY-GATE.md": "references/quality-gate.md",
}


def sync(check=False, root=ROOT):
    failures = []
    for source, relative in FILES.items():
        data = (root / "shared/wealth-quality" / source).read_bytes()
        for name in PACKAGES:
            target = root / "skills/wealth-management" / name / relative
            if check:
                if not target.is_file() or target.read_bytes() != data:
                    failures.append(f"{name}/{relative}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failures = sync(args.check)
    print("Quality bundle drift: " + ", ".join(failures) if failures else f"Quality controls {'verified' if args.check else 'bundled'} in {len(PACKAGES)} packages.")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
