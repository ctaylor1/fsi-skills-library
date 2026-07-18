# Domain Rules — audit-evidence-packager

Orientation references: SOX 404 / COSO 2013 internal-control-over-financial-reporting evidence
practice, PCAOB/IIA workpaper and PBC ("prepared by client") conventions, and evidence
chain-of-custody expectations for internal/external audit and regulatory exams. The
organization's audit plan, its request-to-artifact mapping, and the **remediation config** take
precedence and are versioned contracts. Nothing here is a control conclusion — the skill labels
**packaging readiness** for auditor review.

## Chain of custody (required for every packaged artifact)

An artifact's provenance is certifiable only when its `chain_of_custody` block carries all four
fields: `source_system`, `prepared_by`, `extracted_on`, `checksum`. A missing field ⇒
`custody-gap`. Redaction is logged as a custody action and produces a redacted *copy*; the source
of record is never altered.

## Redaction (enforced before packaging)

Each artifact may declare `sensitive_fields` (PII/NPI columns — e.g. SSN, bank account). An
artifact is **redaction-resolved** only when `redaction.applied` is true and every listed
sensitive field appears in `redaction.redacted_fields`. A flagged-but-unredacted artifact ⇒
`redaction-required` and is never packaged. The package carries masked identifiers and evidence
pointers only — never raw sensitive values. Over-redacting to obscure a responsive artifact is
equally prohibited.

## Period coverage (deterministic)

An artifact **covers** a request when it is not `superseded_by` a newer artifact and its coverage
date (`as_of_date`, else `period.to`) falls within the request's `period`. Out-of-period,
superseded, or undatable ⇒ `evidence-stale`; the stale artifact is still cited so the claim is
supported and the reviewer can refresh it.

## Packaging-readiness status (precedence, per request)

Evaluated in order; the first match wins:

1. **not-applicable** — `not_applicable: true` **and** a documented `na_justification`. Without
   documented justification, the request is **needs-data**.
2. **needs-data** — no `artifact_refs` mapped to the request. Never guess coverage.
3. **evidence-gap** — a referenced artifact is absent from the evidence repository.
4. **redaction-required** — a mapped artifact has flagged sensitive fields that are not fully
   redacted. Redaction is a gate: the item is not packaged until it is resolved and logged.
5. **custody-gap** — a mapped artifact is missing one or more chain-of-custody fields.
6. **evidence-stale** — a mapped artifact does not cover the requested period (out-of-period or
   superseded). The stale evidence is still cited.
7. **packaged-complete** — every mapped artifact is in-period, custody-preserved, and
   redaction-resolved.

Redaction outranks custody, and custody outranks staleness, so a privacy leak or an
untraceable artifact can never be masked by a period check. `packaged-complete` is **not**
"effective" — it means the evidence is assembled and ready for the auditor to test.

## Open items and remediation register

Each `evidence-gap` / `evidence-stale` / `redaction-required` / `custody-gap` request produces one
register row per affected artifact: `request_id`, `artifact_id`, issue, owner, target date, and
severity. Owner/target/severity come from the versioned remediation config when supplied;
otherwise they are `(unassigned)` / `(TBD)` / `medium` and must be completed by the coordinator.

## Hard boundaries (fail closed)

- No **control-effectiveness conclusion** and no **audit opinion** (qualified/unqualified).
- No **management representation / attestation** signing, and no **delivery/submission** of the
  package.
- No **fabricated or inferred evidence**; unmapped ⇒ needs-data, missing ⇒ gap, out-of-period ⇒
  stale.
- No **raw sensitive values** in the package — flagged fields must be redacted; no
  **over-redaction** to withhold an artifact.
- No **altering the source of record** — redaction acts on a copy; custody is preserved.

## Package — required contents

Framework + engagement type; `audit_period` + `as_of_date`; PBC request register;
request-to-artifact-to-evidence mapping with citations; packaging-readiness summary (counts, not a
conclusion); open-items / remediation register; chain-of-custody + redaction log; source/citation
index; approvals block with `delivered_to_auditor: false` and `management_assertion_made: false`;
and the standing non-conclusion note.
