# Domain Rules — pci-dss-evidence-assistant

Orientation references: PCI DSS v4.0.1 (12 requirements across 6 control objectives) and its
SAQ/ROC testing procedures. The organization's PCI program standard, its control-to-
requirement mapping, and the **freshness-window config** take precedence and are versioned
contracts. Nothing here is a compliance determination — the skill labels **evidence
readiness** for a QSA/ISA-led assessment.

## Evidence freshness windows (deterministic; configurable)

Staleness is computed against the package `as_of_date`. An evidence item is **stale** if its
age exceeds the window for its type. Undatable evidence is treated as stale.

| Evidence type | Default window (days) | Typical PCI driver |
| ------------- | --------------------- | ------------------ |
| `asv-scan` | 90 | 11.3.2 quarterly external ASV scan |
| `internal-vuln-scan` | 90 | 11.3.1 quarterly internal scan |
| `pen-test` | 365 | 11.4 annual penetration test |
| `risk-assessment` | 365 | 12.3.x targeted risk analyses |
| `policy-review` | 365 | 12.1.1 annual policy review |
| `config-review` | 180 | 1.2.7 network security control review (6-monthly) |
| `access-review` | 180 | 7.2.4 periodic access reviews |
| `training` | 365 | 12.6 annual security-awareness training |
| `log-review` | 30 | 10.4 periodic audit-log review |
| `na-justification` | 365 | documented N/A justification refresh |
| `default` | 365 | any unmapped evidence type |

Deployment overrides via `freshness_windows` in the input. The applied window version is
recorded on the package.

## Evidence-readiness status (precedence, per requirement)

Evaluated in order; the first match wins:

1. **not-applicable** — `not_applicable: true` **and** a documented `na_justification`.
   Without documented justification, the requirement is **needs-data** (PCI requires N/A to
   be justified).
2. **needs-data** — no control mapped to the requirement. Never guess coverage.
3. **evidence-gap** — one or more mapped controls have **no** in-scope evidence.
4. **evidence-stale** — all mapped controls have evidence, but at least one control's
   evidence is entirely past its freshness window. The stale evidence is still cited so the
   claim is supported and the reviewer can refresh it.
5. **evidence-complete** — every mapped control has current, in-scope evidence.

A gap (missing control) outranks staleness. `evidence-complete` is **not** "In Place" — it
means the evidence is assembled and current, ready for a QSA/ISA to assess.

## Gap and remediation register

Each `evidence-gap` and `evidence-stale` requirement produces one register row per affected
control: `req_id`, `control_id`, issue, remediation owner, target date, and severity. Owner/
target/severity come from the versioned remediation config when supplied; otherwise they are
`(unassigned)` / `(TBD)` / `medium` and must be completed by the program manager.

## Hard boundaries (fail closed)

- No **compliance attestation** and no **In Place / Not In Place** determination.
- No **AOC/ROC/SAQ signing or submission**, and no external transmission of the package.
- No **fabricated or inferred evidence**; unmapped ⇒ needs-data, undatable ⇒ stale.
- No **cardholder data (PAN/SAD)** in the package — pointers and masked identifiers only.
- No **scope validation** — the skill summarizes scope inputs; validating scope is the
  assessor's job.

## Package — required contents

DSS version + SAQ/ROC type; assessment period + `as_of_date`; requirement-to-control-to-
evidence mapping with citations; evidence-readiness summary (counts, not a determination);
gap/remediation register; assumptions/open items; source/citation index; approvals block
with `attestation_made: false`; and the standing non-attestation note.
