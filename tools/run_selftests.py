#!/usr/bin/env python3
"""Run the deterministic evals bundled with each skill.

Reads every skills/**/evals/evals.json, finds evals of type "deterministic" that carry a
"command" and "expect_exit", runs the command from the skill directory, and checks the exit
code (and any "expect_contains" substrings). This turns the eval specs into an executable
regression suite that scales as skills are added.

Usage:
    python tools/run_selftests.py                    # all skills
    python tools/run_selftests.py skills/banking     # a subtree
Exit 0 if all deterministic checks pass, 1 otherwise.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def find_eval_files(targets):
    roots = [(REPO / t) if not Path(t).is_absolute() else Path(t) for t in targets] or [REPO / "skills"]
    files = []
    for r in roots:
        files.extend(sorted(r.rglob("evals/evals.json")))
    return files


def main() -> int:
    files = find_eval_files(sys.argv[1:])
    if not files:
        print("No evals.json files found.")
        return 0
    total_pass = total_fail = 0
    for ef in files:
        skill_dir = ef.parent.parent
        try:
            spec = json.loads(ef.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"FAIL  {skill_dir.name}: cannot parse evals.json ({e})")
            total_fail += 1
            continue
        # Run any eval that is executable: has a shell command and an expected exit code.
        # This covers "deterministic" checks and "safety" fixtures that must fail closed.
        checks = [e for e in spec.get("evals", [])
                  if e.get("command") and "expect_exit" in e]
        if not checks:
            continue
        print(f"[{skill_dir.relative_to(REPO)}]")
        for c in checks:
            proc = subprocess.run(c["command"], cwd=skill_dir, shell=True,
                                  capture_output=True, text=True)
            ok = proc.returncode == c["expect_exit"]
            out = proc.stdout + proc.stderr
            for sub in c.get("expect_contains", []):
                if sub not in out:
                    ok = False
            mark = "PASS" if ok else "FAIL"
            print(f"  {mark}  {c['id']} (exit {proc.returncode}, expected {c['expect_exit']})")
            if ok:
                total_pass += 1
            else:
                total_fail += 1
                if proc.returncode != c["expect_exit"]:
                    print("        exit mismatch")
                for sub in c.get("expect_contains", []):
                    if sub not in out:
                        print(f"        missing expected output: {sub!r}")
    print(f"\nTOTAL: {total_pass} passed, {total_fail} failed")
    return 1 if total_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
