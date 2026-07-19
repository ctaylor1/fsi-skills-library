# Source Map — operational-resilience-reporter

## Source hierarchy (highest first)

| Rank | Source (MCP integration) | Used for | Access |
| ---- | ------------------------ | -------- | ------ |
| 1 | **Critical-service register** (important business services + impact tolerances) | Service identity, IBS scope, tolerance thresholds | Read-only |
| 2 | **Critical-third-party register** (TPRM) | Third-party identity, criticality, contract + exit-plan refs | Read-only |
| 3 | **CMDB / dependency map** | Service→third-party and service→service dependencies, concentration | Read-only |
| 4 | **Incident system** | Incident chronology, severity, metrics, root-cause/remediation refs | Read-only |
| 5 | **Resilience testing system** | Scenario tests, outcomes, within/outside-tolerance results | Read-only |
| 6 | **Contract / exit-plan store** | Contract and exit/contingency evidence for critical third parties | Read-only |
| 7 | **Jurisdictional ruleset + templates** (versioned) | Required report sections, template version, rule pack | Read-only |
| 8 | **Approval / attestation records** | Recorded human approvals and attestation/notification status | Read-only |

The register is the **system of record** for service and third-party identity. The ruleset
and report templates are **versioned contracts** — the pack version is recorded on every
report package for reproducibility and review.

## Citation format

`{system}:{ref}@{date|version}` — e.g. `register:service=IBS-PAY-001@2026-07-18`,
`register:tp=TP-CLOUD-01@2026-07-18`, `cmdb:IBS-PAY-001->TP-CLOUD-01@2026-07-18`,
`incidents:INC-5501@2026-05-02`, `tests:TEST-7001@2026-04-15`,
`ruleset:UK-PRA-SS1-21@opres-rules-2026.07`, `approval:AE-1@2026-07-16`.

## Freshness / effective dates

- Registers, incidents, and tests are read fresh as of `report_request.as_of_date`; the
  reporting period bounds what is summarized.
- Jurisdiction rules and templates are **versioned**; `ruleset_version` and
  `template_version` are recorded on the package. A mismatch between the requested
  jurisdiction and the resolved template pack is a fail-closed condition (surface it, do not
  guess the template).

## Least-privilege operations (deployment)

- `register.read(service_id|tp_id)`, `cmdb.read(service_id)` — read-only.
- `incidents.read(period, service_id)`, `tests.read(period, service_id)` — read-only, bounded.
- `contracts.read(tp_id)` → contract/exit-plan refs — read-only.
- `ruleset.get(jurisdiction, version)` → required sections + template — read-only, versioned.
- `approvals.read(report_ref)` → recorded human approvals — read-only.

No mutation from this skill. It assembles a **draft** package only; recording an approval,
attesting, and any regulatory submission are performed by authorized humans through their
own systems, never by this skill.
