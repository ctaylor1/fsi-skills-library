#!/usr/bin/env python3
"""Deterministic input validation for prompt-and-agent-risk-reviewer.

Validates an agent review package before control evaluation. Fails closed on structural
problems; warns on data-quality gaps (undocumented control blocks) that the review will
treat as controls-not-evidenced.

Input schema (JSON): see references/source-map.md. Key fields:
  review_id, agent_id, as_of (YYYY-MM-DD), control_catalog_version,
  agent{
    purpose, autonomy (autonomous|human-in-the-loop|suggest-only),
    data_classification (Public|Internal|Confidential|Restricted|PII),
    tools[{name, effect(read|write|external|payment|irreversible), scope, scope_broad, human_approval}],
    untrusted_input_surfaces[], instruction_source_boundary,
    memory{persists, persists_untrusted, feeds_prompt},
    retrieval{enabled, sources[{name, trust(trusted|untrusted)}]},
    guardrails{output_filter, dlp, prohibited_behavior_refusal, injection_mediation},
    prohibited_surface[], failure_mode{fail_closed, human_escalation},
    observability{logs_tool_calls, eval_harness}
  }

Usage:
  python validate_input.py agent_review.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("review_id", "agent_id", "as_of", "control_catalog_version", "agent")
AUTONOMY = {"autonomous", "human-in-the-loop", "suggest-only"}
CLASSES = {"Public", "Internal", "Confidential", "Restricted", "PII"}
EFFECTS = {"read", "write", "external", "payment", "irreversible"}
OPTIONAL_BLOCKS = ("memory", "retrieval", "guardrails", "failure_mode", "observability")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    agent = doc.get("agent")
    if not isinstance(agent, dict):
        errors.append("agent must be an object")
        return errors, warnings

    autonomy = agent.get("autonomy")
    if autonomy is None:
        errors.append("agent.autonomy is required")
    elif autonomy not in AUTONOMY:
        errors.append(f"agent.autonomy must be one of {sorted(AUTONOMY)}, got {autonomy!r}")

    dclass = agent.get("data_classification")
    if dclass is None:
        warnings.append("agent.data_classification missing — output-guardrail control assumes sensitive-data gap unproven")
    elif dclass not in CLASSES:
        errors.append(f"agent.data_classification must be one of {sorted(CLASSES)}, got {dclass!r}")

    if not agent.get("purpose"):
        warnings.append("agent.purpose missing — least-privilege review is weakened without a declared purpose")

    tools = agent.get("tools")
    if not isinstance(tools, list) or not tools:
        errors.append("agent.tools must be a non-empty list")
        return errors, warnings

    names = set()
    for i, t in enumerate(tools):
        tag = f"agent.tools[{i}] ({t.get('name','?')})"
        if not t.get("name"):
            errors.append(f"{tag}: missing 'name'")
        if t.get("effect") not in EFFECTS:
            errors.append(f"{tag}: effect must be one of {sorted(EFFECTS)}, got {t.get('effect')!r}")
        nm = t.get("name")
        if nm in names:
            errors.append(f"{tag}: duplicate tool name")
        names.add(nm)
        if t.get("effect") in {"write", "external", "payment", "irreversible"} and "human_approval" not in t:
            warnings.append(f"{tag}: high-impact tool has no 'human_approval' flag — treated as no approval gate")

    for b in OPTIONAL_BLOCKS:
        if b not in agent:
            warnings.append(f"agent.{b} block absent — dependent controls treat missing controls as gaps (data_gaps)")
    if "untrusted_input_surfaces" not in agent:
        warnings.append("agent.untrusted_input_surfaces absent — injection-surface detection relies on retrieval/memory only")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "agent_review_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
