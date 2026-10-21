# Source map and review profile

Reviewed 2026-09-20 for public orientation:

- [AWS strangler fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html): Incremental migration depends on viable seams and access; it is an option, not a universal recommendation.
- [AWS cutover guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/best-practices-migration-cutover/cutover-stage.html): Plan validation, rollback ownership and treatment of changed data. Local gates are review conventions, not mandated requirements.

Inputs must come from authorized process owners, system/API specifications,
versioned data dictionaries, controlled benchmark records, source snapshots,
license/purpose reviews and named acceptance owners as applicable. Require exact
record/version/date/locator and retain contradictory records. No universal source
precedence resolves conflicts: identify the authoritative scope with its owner.

Scripts consume only supplied local JSON and do not fetch locators, connect to
systems, inspect secrets, send records or validate commercial rights. Public
references do not establish current jurisdiction adoption or platform availability.
Synthetic US-TEST records are not a deployment profile. Verify actual versions,
access, purpose, retention and institution rules before real use.
