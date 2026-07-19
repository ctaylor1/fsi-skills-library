# Adjacent-Skill Handoffs — regulatory-change-impact-analyzer

This skill produces a cited **regulatory-change impact assessment** (`assessment_id`) — the
in-scope obligations, their mapping gaps, effective-date/lead-time and conflict findings, and
a recommended disposition — then stops. It does not decide applicability, close the change,
remediate, file, or attest.

## Downstream (route the human/analyst to)

| Downstream skill | When | Handoff artifact |
| ---------------- | ---- | ---------------- |
| `policy-procedure-gap-analyzer` | A mapping gap needs deep policy/procedure gap analysis and drafting scope | `assessment_id` + obligation ids + missing coverage |
| `risk-control-self-assessment-assistant` | Control design/coverage for the new obligations must be re-assessed | `assessment_id` + affected controls |
| `regulatory-reporting-data-validator` | The change alters a regulatory report's required data/fields | `assessment_id` + reporting obligation ids |
| `privacy-impact-assessment-assistant` | The change is a data-privacy instrument needing a PIA/DPIA | `assessment_id` + data elements |
| `regulatory-exam-response-packager` | An examiner requests evidence of how the change was assessed and handled | `assessment_id` + evidence + adjudication record |

## Out of scope — route elsewhere (not this skill)

- **Obligations from a contract** (not a law/regulation/guidance) → `contract-obligation-extractor`.
- **Impact of a model/algorithm change** (not a regulatory instrument) → `model-change-impact-analyzer`.
- **Firm-wide risk assessment** (not a single regulatory change) → `enterprise-risk-assessment-builder`.

## Upstream (may call this skill)

A compliance advisory / horizon-scanning process (human-run, or an approved read-only
monitoring queue) may request an impact assessment for a specific instrument. This skill is
interactive (`aws-fsi-scheduled-agent: no`) and does not itself run as a scheduled monitor.

## Duplicate-execution prevention

- This skill computes and evidences **findings and a recommendation only**; it must not reach
  a compliance determination, resolve a conflict, close the change, remediate, file, or
  attest — those belong to the human adjudicator and the downstream skills.
- Downstream skills reuse the `assessment_id` evidence rather than re-extracting obligations
  or re-testing applicability.
