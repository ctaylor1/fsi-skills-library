# Shared Support Services & Amazon Quick Design Rules

The portfolio depends on reusable platform services (MCP tools) that must **not** be
duplicated inside individual skill packages. A skill's `references/source-map.md` and
`references/controls.md` reference these services rather than reimplementing them.

## Reusable platform services (v2)

1. **Document intelligence** — page, clause, form, field, and version citation.
2. **Entity resolution** — entity, account, policy, security, merchant, model, service,
   and third-party resolution.
3. **Deterministic computation** — calculation, credit spreading, reconciliation, redaction.
4. **Approved-source retrieval** — policy, regulatory, card-network, filed-form, and
   jurisdiction retrieval.
5. **Controlled content library** — owners, effective dates, expiry, and stale-language
   blocking.
6. **Permission / case-state / approval broker** — separating read, draft, propose,
   authorize, execute, verify, and close.
7. **Case management** — chronology, evidence bundle, chain of custody, and
   triage/investigation handoff.
8. **Evaluation harness** — golden-fixture, routing, regression, safety, authorization,
   latency, and cost evaluation.
9. **Observability** — audit trails, records retention, incident response, recertification.
10. **Data governance** — classification, lineage, freshness, residency, purpose, and
    access controls.
11. **Controlled templates & registers** — checklists, spreading taxonomies, rule
    mappings, and regulatory registers.

## MCP and Amazon Quick design rules

- Use **small deterministic tools** with explicit JSON schemas and **durable case/job
  identifiers**.
- Keep operations **below the fixed timeout**; split long work into **resumable stages**.
- **Separate** read, triage, investigate, draft, authorize, execute, verify, close, and
  report operations into distinct tools.
- Default to **Read Only** or **Ask Each Time**. Mutating tools need idempotency,
  validation, verification, and **rollback guidance**.
- **Do not assume** automatic retries or step-up authorization.
- Treat registered operations and rule/content sources as **versioned contracts**.
- Restrict **scheduled agents** to read-only monitoring, freshness checks, briefing, or
  queue creation.

## Environment reality in this repository

The services above are the *target* platform. In this repository, the enterprise
integrations (core banking, OMS/EMS, KYC/AML, claims, ERP/GL, SIEM/SOAR, payment schemes,
model registries, etc.) are **not present**. Therefore:

- Bundled `scripts/` are **deterministic, self-contained** Python that validate or
  transform data conforming to a documented JSON schema, using **de-identified fixtures**
  under `evals/files/`. They do not open network connections or call live systems.
- Each skill's `references/source-map.md` names the MCP integrations and least-privilege
  operations it *would* bind to at deployment time, so integration is a wiring step, not a
  rewrite.
- `compatibility:` frontmatter lists the required integrations for each skill.
