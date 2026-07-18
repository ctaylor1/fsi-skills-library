# FSI Skill Package — AUTHORING PLAN (DRAFT, for owner review)

> Draft skill package for owner review only; this skill does not publish, register, sign off,
> or release any skill into the catalog, does not approve its own output, and every package
> must pass validation and receive the required human approvals before release.

Fill every `{{placeholder}}` from the APPROVED spec and the build standards. Do not assert a
component, source, evaluation, or approval that is not recorded. Do not claim the skill is
validated, approved, or released — those are human decisions captured below.

## 1. Skill identifiers

| Field | Value |
| ----- | ----- |
| Skill id (build request) | {{skill_id}} |
| Skill name (== directory basename) | {{name}} |
| Target directory | {{directory}} |
| Category | {{category}} |
| Archetype / agent pattern | {{archetype}} / {{agent_pattern}} |
| Risk tier / action mode | {{risk_tier}} / {{action_mode}} |
| Build standard version | {{build_standard_version}} |
| Plan status | {{status}} (packageable: {{packageable}}) |

## 2. Frontmatter metadata block (specification-valid)

Rendered from the approved spec; every required `aws-fsi-*` key present, values from the
allowed set, and tier/action-mode/approval mutually consistent.

```yaml
{{frontmatter_block}}
```

Metadata check: {{metadata_status}} (missing keys: {{missing_keys}}; invalid values:
{{invalid_values}}; consistency issues: {{consistency}}).

## 3. Component checklist (required for this archetype + tier)

| Component | Required | Present | Notes |
| --------- | -------- | ------- | ----- |
| SKILL.md | yes | {{present}} | frontmatter + 13 body sections, < 500 lines |
| references/source-map.md | yes | {{present}} | source hierarchy, citations, freshness |
| references/controls.md | yes | {{present}} | tier, prohibited actions, approvals, records |
| references/handoffs.md | yes | {{present}} | adjacent skills, routing, duplicate prevention |
| references/domain-rules.md | {{req_domain_rules}} | {{present}} | thresholds/taxonomies (when domain rules apply) |
| scripts/validate_input.py | yes | {{present}} | schema/completeness, `--selftest`, "N error(s)" |
| scripts/validate_output.py | yes | {{present}} | tier guardrail screen, `--selftest`, fail closed |
| scripts/calculate_or_transform.py | {{req_calc}} | {{present}} | deterministic computation (when present) |
| assets/output-template.* | {{req_template}} | {{present}} | approved deliverable template (Draft & package) |
| evals/evals.json | yes | {{present}} | trigger/routing/golden/deterministic/safety |
| evals/files/ | yes | {{present}} | valid + non-compliant fixtures |
| CHANGELOG.md | yes | {{present}} | version 0.1.0, scope, controls, approvals owed |

Missing required components: {{missing_components}}.

## 4. Source-map plan

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | {{source_system}} | {{source_use}} | Read-only |

Citation format and freshness rules confirmed against the source hierarchy; every asserted
value in the drafted package cites its source. No unsupported assertions.

## 5. Approval checklist (owed before release — none granted by this skill)

| Approval role | Required for this tier | Recorded? | Reference |
| ------------- | ---------------------- | --------- | --------- |
| Product owner | yes | {{recorded}} | {{approval_ref}} |
| Domain SME | yes | {{recorded}} | {{approval_ref}} |
| Control owner | yes | {{recorded}} | {{approval_ref}} |
| Legal / compliance | {{req_legal}} (R3/R4) | {{recorded}} | {{approval_ref}} |
| Model risk | {{req_model_risk}} (R4) | {{recorded}} | {{approval_ref}} |

Readiness claims in this plan must each cite a recorded approval; an unbacked claim is an
unsupported assertion and blocks packaging.

## 6. Reviewer sign-off (required before release)

- [ ] Frontmatter validates; name == directory; description states what/when/boundary.
- [ ] Required components present; references one level deep; body < 500 lines.
- [ ] `validate_skills.py` = 0 error(s), 0 warning(s); `run_selftests.py` all pass.
- [ ] Source hierarchy, citations, freshness/version labels implemented.
- [ ] No unsupported assertions, no release/approval overclaims, standing disclaimer present.
- [ ] Required human approvals recorded (product owner, domain SME, control owner; +legal/model-risk where applicable).

Reviewer: ________________________  Date: ____________  Decision: release / revise / hold
