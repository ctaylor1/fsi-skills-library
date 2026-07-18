# Source Map — claim-denial-appeal-helper

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Denial notice / EOB** (document intelligence) | Denial reason codes, denied lines, stated appeal rights and window | Read-only |
| 2 | **Policy / plan document** (approved-source retrieval, controlled content library) | Governing provisions: medical-necessity definition, exclusions, prior-auth rules, appeal procedure | Read-only |
| 3 | **Claims administration** | Claim, service dates, adjudication history, prior submissions | Read-only |
| 4 | **Clinical / supporting documents** (document intelligence) | Clinical notes, letters of medical necessity, guidelines, corrected coding, proof of timely filing | Read-only |
| 5 | **Underwriting / benefit configuration** (versioned) | Reason→evidence checklist and appeal-window config for the plan | Read-only |

The **denial notice** governs what was denied and why; the **policy/plan document** governs
the rules the appeal argues under. Never substitute the member's recollection for the denial
notice or the plan wording. If the denial notice and the plan document conflict (e.g., the
notice cites an exclusion the plan text does not contain), **cite both and flag for the
reviewer** — do not resolve silently, and do not conclude which side is correct.

## Citation format

`{system}:{ref}@{date}` — e.g. `doc:doc=CN-1120@2026-05-20`, `policy:policy=PLN-GRP-118;sec=4.2`,
`eob=EOB-77;line=1`. Every drafted argument point cites the specific attached document(s);
every supporting provision cites the plan section.

## Freshness / effective dates

- The **appeal window** and the **reason→evidence checklist** are a versioned config
  contract (owned by the plan/benefit team); the output records the values used so a package
  is reproducible.
- The **appeal deadline** is computed as `denial_date + appeal_window_days` and stated
  explicitly with `days_remaining` as of the run date. Always confirm the operative window on
  the denial notice — plan, jurisdiction, and appeal level can change it.
- Use the plan document **in effect on the date of service**, not the current version, when
  they differ.

## Least-privilege operations (deployment)

- `docs.get(denial_notice_id)` → denial reasons, denied lines, stated appeal rights.
- `policy.get(plan_id, section, as_of)` → governing provisions effective on the service date.
- `claims.get(claim_id)` → adjudication history and prior submissions.
- `docs.list(claim_id)` → available supporting documents (types + citations).
- `config.get('appeal', plan_id, version)` → appeal window + reason→evidence checklist.

All read-only, deterministic, below the fixed timeout, keyed to a durable `appeal_id`; page
long document sets as resumable stages. No write, submit, or file operation is bound.
