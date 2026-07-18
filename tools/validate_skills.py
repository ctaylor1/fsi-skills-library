#!/usr/bin/env python3
"""Validate FSI skill packages against the Agent Skills spec + this library's standards.

Checks per skill:
  - name/description spec constraints; name == parent directory name
  - license present; compatibility <= 500 chars if present
  - metadata is a string->string map; required aws-fsi-* keys present with allowed values
  - referenced files (references/ scripts/ assets/ evals/) exist, are inside the skill,
    and are one level deep (no '..', no chained nesting)
  - SKILL.md body under 500 lines (warning)
  - name/category consistent with catalog/skills-catalog.json when available

Usage:
    python tools/validate_skills.py                 # whole library
    python tools/validate_skills.py skills/banking/account-anomaly-screener [...]
Exit code 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^(?!-)(?!.*--)[a-z0-9-]+(?<!-)$")
SKILL_TYPES = {
    "Artifact-creation skills", "Utility skills", "Workflow or orchestration skills",
    "System-interaction or operational skills", "Analysis and evaluation skills",
    "Guidance or domain-expertise skills",
}
REQUIRED_META = {
    "aws-fsi-category", "aws-fsi-skill-type", "aws-fsi-risk-tier", "aws-fsi-archetype",
    "aws-fsi-agent-pattern", "aws-fsi-delivery-wave", "aws-fsi-action-mode",
    "aws-fsi-scheduled-agent", "aws-fsi-baseline-status", "aws-fsi-human-approval",
    "aws-fsi-data-classification", "aws-fsi-jurisdictions", "aws-fsi-owner",
    "aws-fsi-primary-user", "aws-fsi-version", "aws-fsi-recertification-date",
}
ALLOWED = {
    "aws-fsi-risk-tier": {"R1", "R2", "R3", "R4"},
    "aws-fsi-skill-type": SKILL_TYPES,
    "aws-fsi-scheduled-agent": {"no", "read-only-monitoring"},
    "aws-fsi-human-approval": {"none", "external-delivery", "required"},
    "aws-fsi-baseline-status": {"new", "existing-updated", "existing-no-changes"},
    "aws-fsi-action-mode": {
        "Read-only analysis", "Draft-only; no system-of-record change",
        "Scheduled read-only; alert only", "Approval-gated write or submission",
    },
}
REF_RE = re.compile(r"(?:\]\(|\b)((?:references|scripts|assets|evals)/[^\s\)\]`\"']+)")


def load_catalog():
    p = REPO / "catalog" / "skills-catalog.json"
    if not p.exists():
        return {}
    return {s["name"]: s for s in json.loads(p.read_text(encoding="utf-8"))["skills"]}


def split_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm = text[3:end].strip("\n")
    body = text[end + 4:]
    return fm, body


def validate_skill(skill_dir: Path, catalog: dict):
    errors, warnings = [], []
    rel = skill_dir.relative_to(REPO)
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return [f"{rel}: missing SKILL.md"], []

    text = md.read_text(encoding="utf-8")
    fm_raw, body = split_frontmatter(text)
    if fm_raw is None:
        return [f"{rel}: missing YAML frontmatter"], []

    try:
        import yaml
        fm = yaml.safe_load(fm_raw)
    except ImportError:
        return [], [f"{rel}: PyYAML not installed; skipped frontmatter parse (pip install pyyaml)"]
    except Exception as e:
        return [f"{rel}: frontmatter is not valid YAML: {e}"], []

    name = fm.get("name")
    if not name:
        errors.append(f"{rel}: missing 'name'")
    else:
        if not NAME_RE.match(name) or len(name) > 64:
            errors.append(f"{rel}: 'name' violates spec constraints: {name!r}")
        if name != skill_dir.name:
            errors.append(f"{rel}: 'name' ({name!r}) != directory ({skill_dir.name!r})")

    desc = fm.get("description")
    if not desc or not str(desc).strip():
        errors.append(f"{rel}: missing/empty 'description'")
    elif len(str(desc)) > 1024:
        errors.append(f"{rel}: 'description' exceeds 1024 chars ({len(str(desc))})")

    if not fm.get("license"):
        warnings.append(f"{rel}: no 'license' field")
    comp = fm.get("compatibility")
    if comp and len(str(comp)) > 500:
        errors.append(f"{rel}: 'compatibility' exceeds 500 chars ({len(str(comp))})")

    meta = fm.get("metadata") or {}
    if not isinstance(meta, dict):
        errors.append(f"{rel}: 'metadata' must be a mapping")
    else:
        for k, v in meta.items():
            if not isinstance(v, str):
                errors.append(f"{rel}: metadata['{k}'] must be a string (spec), got {type(v).__name__}")
        missing = REQUIRED_META - set(meta)
        if missing:
            warnings.append(f"{rel}: missing metadata keys: {', '.join(sorted(missing))}")
        for k, allowed in ALLOWED.items():
            if k in meta and meta[k] not in allowed:
                errors.append(f"{rel}: metadata['{k}']={meta[k]!r} not in {sorted(allowed)}")

    # file references one level deep and existing
    for m in REF_RE.finditer(body):
        ref = m.group(1)
        if ".." in ref.split("/"):
            errors.append(f"{rel}: reference escapes skill dir: {ref}")
            continue
        parts = ref.split("/")
        if len(parts) > 3:  # e.g. evals/files/x.json is allowed (2 dirs deep for fixtures)
            warnings.append(f"{rel}: reference is deeply nested (keep one level): {ref}")
        target = skill_dir / ref
        if not target.exists():
            errors.append(f"{rel}: referenced file does not exist: {ref}")

    if body.count("\n") > 500:
        warnings.append(f"{rel}: SKILL.md body exceeds 500 lines ({body.count(chr(10))})")

    if name and name in catalog:
        cat_display = meta.get("aws-fsi-category")
        if cat_display and cat_display != catalog[name]["category"]:
            errors.append(f"{rel}: category {cat_display!r} != catalog {catalog[name]['category']!r}")
    elif name and catalog:
        warnings.append(f"{rel}: name not found in catalog")

    return errors, warnings


def discover(targets):
    dirs = []
    if targets:
        for t in targets:
            p = (REPO / t) if not Path(t).is_absolute() else Path(t)
            if (p / "SKILL.md").exists():
                dirs.append(p)
            else:
                dirs.extend(sorted(d.parent for d in p.rglob("SKILL.md")))
    else:
        dirs = sorted(d.parent for d in (REPO / "skills").rglob("SKILL.md"))
    return dirs


def main() -> int:
    catalog = load_catalog()
    dirs = discover(sys.argv[1:])
    if not dirs:
        print("No skills found to validate.")
        return 0
    all_err, all_warn = [], []
    for d in dirs:
        e, w = validate_skill(d, catalog)
        all_err += e
        all_warn += w
    for w in all_warn:
        print("WARN ", w)
    for e in all_err:
        print("ERROR", e)
    print(f"\nValidated {len(dirs)} skill(s): {len(all_err)} error(s), {len(all_warn)} warning(s).")
    return 1 if all_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
