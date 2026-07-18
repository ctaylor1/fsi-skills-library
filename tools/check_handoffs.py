#!/usr/bin/env python3
"""Check that adjacent-skill handoff references point to skills that exist in the catalog.

Agents sometimes invent plausible-but-nonexistent adjacent-skill names. This scans each
skill's SKILL.md and references/handoffs.md for backtick-quoted, skill-name-shaped tokens
(kebab-case ending in a known skill suffix) and flags any that are not in
catalog/skills-catalog.json.

Usage:
    python tools/check_handoffs.py                 # whole library
    python tools/check_handoffs.py skills/banking   # a subtree or skill dir
Exit 0 if no dangling references, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUFFIX = re.compile(
    r"-(analyzer|reviewer|builder|assistant|checker|monitor|packager|drafter|investigator|"
    r"tracker|reconciler|resolver|optimizer|screener|summarizer|explainer|comparator|"
    r"classifier|maintainer|documenter|composer|preparer|helper|diagnoser|processor|"
    r"adjuster|verifier|designer|interpreter|breakdown|precheck|scanner|spotter|normalizer|"
    r"responder|mapper|generator|coordinator|tester|reporter|briefer|planner|orchestrator|"
    r"advisor|curator|validator|extractor|modeler)$"
)
TOKEN = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`")
# hyphenated non-skill terms that legitimately appear in backticks
ALLOW = {
    "read-only", "draft-only", "system-of-record", "aws-fsi", "case-state", "plan-hash",
    "no-advice", "approval-gated", "fail-closed", "self-test", "no-op",
}


def catalog_names():
    p = REPO / "catalog" / "skills-catalog.json"
    return {s["name"] for s in json.loads(p.read_text(encoding="utf-8"))["skills"]}


def scan(skill_dir: Path, names: set) -> dict:
    dangling = {}
    for rel in ("SKILL.md", "references/handoffs.md"):
        f = skill_dir / rel
        if not f.exists():
            continue
        for m in TOKEN.findall(f.read_text(encoding="utf-8")):
            if m in ALLOW or m in names:
                continue
            if SUFFIX.search(m):
                dangling.setdefault(m, []).append(rel)
    return dangling


def discover(targets):
    if targets:
        out = []
        for t in targets:
            p = (REPO / t) if not Path(t).is_absolute() else Path(t)
            if (p / "SKILL.md").exists():
                out.append(p)
            else:
                out.extend(sorted(d.parent for d in p.rglob("SKILL.md")))
        return out
    return sorted(d.parent for d in (REPO / "skills").rglob("SKILL.md"))


def main() -> int:
    names = catalog_names()
    dirs = discover(sys.argv[1:])
    total = 0
    for d in dirs:
        dangling = scan(d, names)
        if dangling:
            print(f"[{d.relative_to(REPO)}]")
            for ref, locs in sorted(dangling.items()):
                print(f"  NOT IN CATALOG: {ref}  ({', '.join(sorted(set(locs)))})")
                total += 1
    print(f"\n{total} dangling adjacent-skill reference(s) across {len(dirs)} skill(s).")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
