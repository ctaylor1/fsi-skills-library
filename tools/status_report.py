#!/usr/bin/env python3
"""Report build coverage: which catalog skills have a SKILL.md, grouped by wave/category.

Usage:
    python tools/status_report.py            # summary + next-to-build
    python tools/status_report.py --list     # also list every skill's built/pending state
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WAVE_ORDER = [
    "Wave 1 — stabilize existing", "Wave 1 — platform controls",
    "Wave 1 — low-risk productivity", "Wave 2 — analytical production",
    "Wave 3 — regulated casework", "Wave 4 — gated orchestration",
]


def built_names() -> set[str]:
    return {d.parent.name for d in (REPO / "skills").rglob("SKILL.md")}


def main() -> int:
    cat = json.loads((REPO / "catalog" / "skills-catalog.json").read_text(encoding="utf-8"))
    skills = cat["skills"]
    built = built_names()

    by_wave = defaultdict(list)
    for s in skills:
        by_wave[s["delivery_wave"]].append(s)

    total_built = sum(1 for s in skills if s["name"] in built)
    print(f"Coverage: {total_built}/{len(skills)} skills built "
          f"({100*total_built/len(skills):.0f}%)\n")
    print(f"{'Delivery wave':<34} {'built':>6} {'total':>6}")
    print("-" * 48)
    for wave in WAVE_ORDER + [w for w in by_wave if w not in WAVE_ORDER]:
        group = by_wave.get(wave, [])
        if not group:
            continue
        b = sum(1 for s in group if s["name"] in built)
        print(f"{wave:<34} {b:>6} {len(group):>6}")

    # next to build: earliest incomplete wave
    for wave in WAVE_ORDER:
        pending = [s["name"] for s in by_wave.get(wave, []) if s["name"] not in built]
        if pending:
            print(f"\nNext wave with pending work: {wave} ({len(pending)} pending)")
            for n in pending[:15]:
                print(f"  - {n}")
            if len(pending) > 15:
                print(f"  ... and {len(pending)-15} more")
            break

    if "--list" in sys.argv:
        print("\nAll skills:")
        for s in skills:
            mark = "x" if s["name"] in built else " "
            print(f"  [{mark}] {s['delivery_wave'][:14]:<14} {s['category'][:20]:<20} {s['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
