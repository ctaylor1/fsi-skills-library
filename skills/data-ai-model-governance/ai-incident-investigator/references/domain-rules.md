# Domain Rules — ai-incident-investigator

Orientation references: NIST AI Risk Management Framework (Govern/Manage — incident
response), SR 11-7 model-risk governance principles, and the firm's AI/model-risk policy and
incident taxonomy. The firm's policy and its **severity + routing config** take precedence
and are versioned contracts. Nothing here authorizes a determination, closure, or filing —
those are human decisions.

## Incident taxonomy (`incident_class`)

| Class | Example | Severity base | Escalation floor |
| ----- | ------- | ------------- | ---------------- |
| `harmful` | Unsafe/harmful generated output | +3 | — |
| `unauthorized` | Agent acted outside approved scope | +4 | floor SEV-2 |
| `privacy` | PII/NPI exposure to the wrong party | +4 | floor SEV-2 + containment referral |
| `security` | Prompt-injection / data-access breach | +4 | floor SEV-2 + containment referral |
| `biased` | Disparate outcomes on a protected-class proxy | +3 | — |
| `incorrect` | Materially wrong output | +2 | — |
| `resilience` | Availability/degradation of an AI service | +2 | — |

## Severity scoring (deterministic, documented)

Severity is computed from explainable inputs; the mapping is configuration, not judgment.

| Input | Contribution (default) |
| ----- | ---------------------- |
| Incident class | see taxonomy base above |
| Affected population | ≥ 100k +4, ≥ 10k +3, ≥ 1k +2, ≥ 100 +1 |
| Financial exposure | ≥ 1M +3, ≥ 100k +2, ≥ 10k +1 |
| Customer-facing | +2 |
| Regulated decision affected | +3 |
| Data classification | Restricted +3, Highly Confidential +2, Confidential +1 |
| Not reversible | +2 |
| Detection latency | > 30 days +2, > 7 days +1 |

Bands: **SEV-1 (Critical)** score ≥ 10; **SEV-2 (High)** score 5–9 **or** an escalation-class
floor (`privacy`/`security`/`unauthorized`); **SEV-3 (Moderate)** otherwise. Severity is a
triage rank for a human, not a determination of cause or fault.

## Root-cause hypotheses (never determinations)

The engine emits **candidate hypotheses** by `root_cause_hypothesis_category` (`model`,
`data`, `prompt-agent-design`, `permissions`, `infrastructure`, `third-party`, `unknown`),
each tied to an evidence reference and worded as "may have contributed … required before any
determination." The determination is reserved for the human adjudicator.

## Disposition rules (recommendations only)

| Disposition | Condition |
| ----------- | --------- |
| `needs-evidence` | Timeline events or impact estimate missing (never guess) |
| `recommend-containment-referral` | `privacy` or `security` class (route to IR/DLP) |
| `recommend-escalate-for-adjudication` | SEV-1 or SEV-2 (and not a containment class) |
| `recommend-remediation-owner` | SEV-3 (route to the model/data owner for tracking) |

## Hard boundaries (fail closed)

- No **incident closure**, **root-cause determination**, or **model exoneration/redeployment**.
- No **regulatory or breach notification** drafting, sending, or filing.
- No **containment action** — refer to IR/DLP; the skill never isolates or disables a system.
- No **auto-merge** of related incidents; linking is for human review.

## Evidence bundle — required contents

Durable `case_id`; ordered chronology (each entry cited); implicated model/agent + owner;
parties (aggregate affected count only); impact estimate (population, exposure, data
classification, reversibility); candidate root-cause hypotheses; recommended routing; linked
prior incidents; citations for every item; recommended severity band.
