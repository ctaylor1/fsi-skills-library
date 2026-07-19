# Domain Rules — model-validation-assistant

Orientation references: SR 11-7 / OCC 2011-12 (model risk management — the three core validation
elements: conceptual soundness, ongoing monitoring, outcomes analysis), NIST AI RMF, and ISO/IEC
42001. The firm's **model risk framework / validation standard** takes precedence and is a
versioned contract (`framework_version`). All derivations below are configuration, not judgment —
a validator may override during adjudication, but the draft states the computed value.

## Required validation areas (all seven, always assessed)

`conceptual_soundness`, `data`, `performance`, `outcomes`, `limitations`, `controls`,
`monitoring`. A pack missing any area is `needs-data`, not a completed validation.

## Independence rule (the core control)

Independent validation must rest on the validator's own evidence, not the developer's assertion.
For each area:

- A declared **`pass`** is credited as validated **only when** `independent_evidence: true`
  **and** a `source_ref` is present, **and** no recorded test is `fail` or `inconclusive`.
- A `pass` that is only developer-attested (`independent_evidence: false`), or that carries an
  `inconclusive` test, is downgraded to **`not_tested`** — a coverage/independence gap.
- Any recorded test with outcome `fail` forces the area to **`deficiency`**, regardless of the
  declared status (independent evidence contradicts the claim).
- A control or test with no `evidence_ref` is **unproven** and earns no independent credit.

Effective status is therefore one of: `pass` (independently validated), `deficiency` (weakness
evidenced), or `not_tested` (not independently covered).

The engine records this independence decision explicitly on each area as an
`independently_sourced` boolean (`independent_evidence` **and** a `source_ref`). The output screen
(`scripts/validate_output.py`) enforces the credited-`pass` gate and the deterministic tie-out
against that **same** carried flag — not a re-derived proxy such as "has any citation" — so the
engine and the guardrail cannot drift apart, and a missing/false flag fails closed.

## Findings (open items requiring adjudication)

A finding is generated for every area whose effective status is `deficiency` or `not_tested`
(`pass` areas produce none):

- `deficiency` → `finding_type: deficiency`.
- `not_tested` → `finding_type: coverage-gap` (includes developer-attested-only passes).

Each finding carries: `area`, `finding_type`, `severity` (= the area's `materiality`), the gap's
`recommended_remediation` (from the area's `recommended_action`, else an area default), an
`owner`, `source_refs`, `status: open`, and `adjudication_required: true`. Severity tracks
materiality: `High` / `Medium` / `Low`. A finding is **never** closed, resolved, or waived here.

## Overall severity, recommended disposition, and approver routing

`overall_finding_severity` = the **highest** finding severity across the seven areas
(highest-wins; `None` if no findings). The disposition is a **recommendation only** — never a
decision — and the validation outcome is always emitted `pending`:

| Overall severity | recommended_disposition | Required approvers |
| ---------------- | ----------------------- | ------------------ |
| **High** | `material-findings-remediation-required` | Model Risk Committee; Chief Risk Officer (or delegate) |
| **Medium** | `findings-remediation-recommended` | Head of Model Validation; Model Owner |
| **Low** | `minor-findings-noted` | Head of Model Validation |
| **None** | `no-findings-open` | Head of Model Validation |

`model_tier` (from the inventory) is recorded as context; per-area `materiality` already reflects
the model's importance, so severity is driven by materiality, not re-derived from the tier.

## Hard boundaries (fail closed)

- No **approval, certification, or clearance of a model for use / production**.
- No **final / binding validation decision or rating**; the disposition is a computed
  recommendation the validator adjudicates.
- No **closing / resolving / waiving** a finding.
- No **assembling, finalizing, or filing the governed model documentation pack** — that is a
  separate control activity (`model-risk-documenter`); this skill produces validation findings.
- No **unsupported assertion**: every area cited; every finding sourced and remediated; every
  credited `pass` independently evidenced.
- No **guessing**: a missing area, status, or materiality is `needs-data`.
