# Controls — operational-resilience-reporter

- **Risk tier:** R3 — regulated/control decision support. **Action mode:** Draft-only; no
  system-of-record change. The skill assembles a draft report package; it writes nothing to
  any register, incident system, or regulator.
- **Human approval:** `required` — a named accountable executive (first line) and a
  second-line reviewer must adjudicate the draft; any regulatory notification, attestation,
  or submission is a separate human act performed outside this skill.

## Prohibited (fail closed)

- **Regulatory submission or filing** to any supervisor (PRA/FCA, ECB/DORA competent
  authority, US agencies) — the skill drafts only.
- **Attestation on behalf of a person or the board** ("we attest", "board has attested",
  "hereby certify").
- **Resilience/compliance determinations** ("we determine we are compliant",
  "no notification required", "no further action", "matter/case closed").
- **Fabricated evidence** — a `gap` section must never carry content; a `drafted` section
  must never lack a citation.
- **Overwriting the register or incident/test records** (identity, tolerances, chronology).

## Report states (this skill may set only these)

A section is `drafted` (evidence-cited facts) or `gap` (no evidence in dataset; requires
human input). The package as a whole is a **draft** — it never carries a state of `filed`,
`submitted`, `attested`, `certified`, or `determined-compliant`.

## Required output screens (`scripts/validate_output.py`)

- **Template fidelity** — every required section for the `report_type` + `jurisdiction` is
  present (base template + jurisdiction pack).
- **No unsupported/unapproved claims** — `unsupported_claims` empty; each `drafted` section
  has ≥1 fact and ≥1 citation; each `gap` section has no content/citations.
- **Impact-tolerance tie-out** — `breached` equals the deterministic `observed` vs
  `threshold` comparison (by tolerance direction).
- **Required approvals recorded** — `accountable-executive` and `second-line-review` each
  present, `approved`, with a name and date; missing/incomplete → fail closed.
- **Language screen** — no filing/submission/attestation/determination/closure language
  (factual "impact tolerance breached" is allowed by design).
- **Draft watermark + standing note** present.

## Segregation of duties

Drafting is separate from adjudication, attestation, and filing. The skill (or the analyst
operating it) does not also attest or submit; the accountable executive and second line
adjudicate, and an authorized regulatory-reporting human files.

## Data classification, privacy, records

- **Confidential (security-sensitive).** Registers, dependency maps, and incident detail
  reveal control weaknesses; mask internal identifiers to what the report requires.
- Retain the draft package, its citations, the `ruleset_version`/`template_version`, and the
  recorded approvals so the deliverable is reproducible and reviewable.
- Log the author identity and every read on registers/incidents/tests/contracts.
